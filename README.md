# Peblo TV Mini

CMS upload → published catalogue → Netflix-style browse. Three layers (API,
CMS, Viewer) plus the publish pipeline that connects them.

## Prerequisites

- Docker and Docker Compose (v2, the `docker compose` plugin — this repo
  uses `docker-compose.yml` which also works with the older standalone
  `docker-compose` binary).
- Nothing else is required to run the whole stack — Python, Node, and
  Postgres all run inside containers.

If you want to run pieces outside Docker (e.g. for faster iteration):
- Python 3.12 + pip (backend)
- Node.js 20 + npm (cms, viewer)
- PostgreSQL 16, or just point `DATABASE_URL` at a local SQLite file for
  quick experiments — the backend falls back to SQLite automatically if
  `DATABASE_URL` isn't set.

## Ports (all changed from their usual defaults)

| Service          | Default | This project | Why |
|-------------------|---------|--------------|-----|
| PostgreSQL         | 5432    | **55432**    | avoid clashing with any local Postgres |
| API (FastAPI)      | 8000    | **8088**     | avoid clashing with other local dev APIs |
| CMS (Vite dev)     | 5173    | **5180**     | avoid clashing with default Vite apps |
| Viewer (Vite dev)  | 5173/4  | **5190**     | avoid clashing with CMS and other Vite apps |

## Run it

```bash
cp .env.example .env
docker-compose up --build
```

This brings up, seeded and working:
- **API** on http://localhost:8088 (health check: `GET /health`)
- **CMS** on http://localhost:5180 — open Settings first and paste an API key
  (`editor-key-change-me` or `admin-key-change-me` from `.env`, or your own
  values if you changed them)
- **Viewer** on http://localhost:5190 — nothing to configure, it's public

The API container seeds demo data on first boot (2 published shows — one
clean, one with deliberate validation issues — and 1 draft show). Nothing
is published to the catalogue until you hit **Publish** in the CMS, so the
Viewer starts empty until you do that.

### Suggested first flow
1. Open the CMS → Settings → paste the **admin** key.
2. Go to **Publish** → see the validation report surface the seeded issues
   (missing durations, missing thumbnails, missing poster/banner images).
   Publish is blocked while *any* issue exists — that's intentional, so you
   can see the report doing its job on real broken data.
3. To actually get past that block without manually uploading real images
   for every seeded show, run the demo fixer once the containers are up:
   ```bash
   docker-compose exec api python -m seed.fix_demo_data
   ```
   This adds correctly-sized placeholder poster/banner/thumbnail images and
   fills the one missing duration — it does NOT touch the deliberate issues
   in `seed.py` itself, so re-running `docker-compose up --build` (which
   re-seeds) will bring the issues back until you run the fixer again.
4. Reload the CMS Publish tab → 0 blocking issues → **Publish catalogue**.
5. Open the Viewer → the published shows now appear with their rows, hero,
   and search.

### Running tests
```bash
cd backend && pip install -r requirements.txt && pytest -q
```
15 tests cover: role enforcement (editor vs admin, actually blocking
requests — not just declared), publish blocking on validation issues,
`content_group` → single catalogue entry with a `languages` list, Season 0
excluded from normal seasons, and artwork validation (aspect ratio, size
ceiling).

---

## Decisions & trade-offs

- **Auth is a static `X-API-Key` → role mapping**, not JWT/OAuth. This
  demonstrates real, enforced role checks (not just declared ones) without
  building a full user system, which was out of scope for a mini. A real
  Peblo deployment would swap this for the actual identity provider; only
  `app/core/auth.py` would change.
- **`Base.metadata.create_all()` instead of Alembic migrations.** Faster to
  get right for a fixed, small schema; a real project would use Alembic
  from day one so schema changes are reviewable and reversible.
- **Search is in-memory over the published catalogue JSON**, not a DB
  query or search index. See Part E below for exactly where this breaks
  down and what replaces it.
- **CMS auth UX is a pasted key in Settings**, not a login screen — kept
  deliberately minimal since the API auth itself is already simplified.

## Part E — Written

**How publishing is atomic, and what happens if the process dies mid-publish.**
The publish job builds the whole catalogue in memory, serializes it once,
then writes it via `storage.atomic_write_bytes()`. On local disk this
writes to a temp file in the same directory and calls `os.replace()`,
which is atomic on POSIX and Windows — a reader either sees the complete
old file or the complete new file, never a partial one. On S3-compatible
storage (R2/MinIO) a single `PUT` is already atomic from a reader's
perspective, so we stage to a `.staging` key and copy it into place, then
delete the staging object. If the process dies before the write completes,
the live `catalogue.json` is untouched and readers keep serving the last
good publish — nothing is ever half-written. The `PublishRun` row is
inserted as `"running"` before the write and updated to `"success"` or
`"failed"` after; if the process dies between the file write succeeding
and that final commit, the file is correct but the run row is stuck at
`"running"`. That's a known gap: a stuck-run detector (treat any `"running"`
run older than N minutes as failed, prompting a re-publish) is a
documented follow-up, not implemented here.

**Storage abstraction — what changes to move from local disk to
Cloudflare R2?** Nothing above `app/storage/`. `StorageBackend` is an
abstract interface (`write_bytes`, `read_bytes`, `exists`,
`atomic_write_bytes`, `url_for`); `LocalDiskStorage` and
`S3CompatibleStorage` both implement it, and `app/storage/__init__.py`
picks one based on `STORAGE_BACKEND`. Moving to R2 means setting
`STORAGE_BACKEND=s3` plus the four `STORAGE_S3_*` variables (R2 speaks the
S3 API). The only behavioral differences worth calling out: R2 has zero
egress fees, so serving artwork/catalogue reads directly from R2 stops
being a cost concern the way S3 egress would be; and `url_for` on S3 mode
returns a presigned URL instead of a static path, so anything caching URLs
long-term would need to switch to public bucket URLs or re-sign.

**Search — how it's implemented, where it stops working, what's next.**
`/catalog/search` loads the published `catalogue.json` and filters it in
memory: substring match on show/episode title and category, plus
`language`/`section` filters that all compose. This is fine at the scale
this catalogue realistically lives at — hundreds of shows, a few thousand
episodes, a JSON file well under a megabyte. It stops working gracefully
once the catalogue grows to the point where deserializing and scanning it
on every request adds meaningful latency, roughly high hundreds of KB to
low MB of JSON, or once someone wants ranked/fuzzy results instead of
substring matches. The next step would be a proper search index (Postgres
full-text search with a `tsvector` column populated at publish time, or an
external index like Meilisearch/Typesense if relevance ranking or typo
tolerance matters) built from the same publish step, so the read path
stays fast and the write path stays simple.

**Why serve a pre-published catalogue file instead of querying the
database per request? Where does that choice bite you?** A viewer-facing,
child-facing surface needs to be fast and resilient regardless of what's
happening in the CMS or database — a slow admin query, a mid-edit show, or
a DB hiccup shouldn't be visible to a kid browsing. Publishing a flat file
also gives a natural point-in-time snapshot: everyone sees the same
catalogue until the next publish, which is easy to reason about and cheap
to serve or CDN-cache. It bites you in two places: (1) staleness — an
editor who just fixed something has to remember to hit Publish, and there
is no "preview my unpublished change" path in this build; and (2) it
duplicates data (DB is the source of truth, the file is a derived copy),
so any future feature that needs live state — e.g. "show a badge if this
episode was just added today" — either needs to bake that into the
publish step or accept it'll be off by up to one publish cycle.

**What was left out, and why.** No Alembic migrations (see Decisions
above). No versioned catalogue / rollback / diff / audit log — all three
stretch items were skipped in favor of getting Parts A–D solid; the
`PublishRun` table already records who/when/counts/outcome, which is the
minimum scaffolding a rollback feature would build on. No real user
accounts — static API keys stand in for auth. No CDN/production
deployment target — the GitHub Actions deploy step is written and
explained but not wired to a real cloud account, per the challenge's own
allowance. Search is substring-only, not fuzzy/ranked (see above).

**Which AI tools were used, and where output was accepted or rejected.**
This implementation was built with Claude (Anthropic) end-to-end,
generating the FastAPI backend, both React frontends, the docker-compose
setup, CI workflow, and this README, based directly on the challenge
document. Where AI-suggested approaches were adjusted: the S3 backend's
`atomic_write_bytes` initially assumed in-place partial writes were
possible on S3, which isn't accurate — this was corrected to the
stage-then-copy approach described above once the actual S3 object model
was considered. Ambiguous points (e.g. exact validation-report grouping
granularity, whether `/admin/validation-report` should be editor- or
admin-only) were resolved with an explicit decision rather than a
follow-up question, per the challenge's own instruction to do that and
note it — both are called out inline in code comments.

## Secrets in production

For local dev, `.env` (git-ignored) is fine. In production: API keys /
DB credentials / S3 credentials would live in a secrets manager (AWS
Secrets Manager, GCP Secret Manager, or Doppler/1Password for smaller
teams), injected into the container at deploy time as environment
variables — never baked into the image or committed. The GitHub Actions
workflow would pull them from encrypted repo/environment secrets for the
deploy step. Rotation would be handled by the secrets manager, not by
hand-editing `.env` files.

## What to alert on

**Publish failure rate.** A failed `PublishRun` (`outcome == "failed"`) is
the single highest-signal event in this system: it means content the CMS
team believes is live isn't actually reflected in what viewers see, with
no other visible symptom (the site doesn't go down, it just goes stale).
Alerting on `/admin/catalog/runs` showing any `"failed"` outcome, or on no
successful run in an unexpectedly long window, catches both an active bug
and the "editor thinks they published but nothing happened" case before a
content team notices something's missing on their own.

## Time spent (rough)

- Part A (backend): ~40%
- Part B (CMS): ~20%
- Part C (Viewer): ~15%
- Part D (pipeline/ops): ~15%
- Part E (this README) + polish: ~10%
