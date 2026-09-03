"""
Builds the published catalogue and writes it atomically.

Atomicity strategy (see README Part E for the full write-up):
  1. Compute the whole catalogue dict in memory from the current DB state.
  2. Serialize it once.
  3. Call storage.atomic_write_bytes(), which stages the bytes under a
     temp key and then does a single atomic rename/copy into the real
     "catalog/catalogue.json" key.
  4. Only after that succeeds do we mark the PublishRun as "success" and
     commit. If the process dies at any point before step 3 completes,
     the live catalogue.json is untouched -- readers keep serving the
     previous good publish. If it dies between step 3 and the DB commit,
     the *file* is already correct; on restart the run row would still
     show "running", which the admin UI should treat as "assume failed,
     re-publish" (a stuck-run detector, not implemented here, is a
     documented follow-up).
"""
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import PublishRun, PublishStatus, Show
from app.services.validation_report import build_validation_report
from app.storage import get_storage

CATALOGUE_KEY = "catalog/catalogue.json"


class PublishBlockedError(Exception):
    def __init__(self, issue_count: int):
        self.issue_count = issue_count
        super().__init__(f"{issue_count} validation issue(s) block publish.")


def _build_catalogue_dict(db: Session) -> dict:
    shows = (
        db.query(Show)
        .filter(Show.status == PublishStatus.published)
        .order_by(Show.title.asc())  # deterministic ordering
        .all()
    )

    sections: dict[str, list[dict]] = {}
    episodes_count = 0

    for show in shows:
        # Group episodes by content_group across all non-trailer seasons.
        # Season 0 is trailers and is surfaced separately, never as a
        # normal season, and never merged into a content_group.
        entries_by_group: dict[str, dict] = {}
        ungrouped_episodes: list[dict] = []
        trailers: list[dict] = []

        for season in sorted(show.seasons, key=lambda s: s.number):
            for ep in sorted(season.episodes, key=lambda e: e.episode_number):
                if ep.status != PublishStatus.published:
                    continue
                episodes_count += 1
                thumb = next((a for a in ep.artworks if a.kind == "thumbnail"), None)
                ep_payload = {
                    "id": ep.id,
                    "title": ep.title,
                    "episode_number": ep.episode_number,
                    "season_number": season.number,
                    "duration_seconds": ep.duration_seconds,
                    "thumbnail_key": thumb.storage_key if thumb else None,
                }

                if season.number == 0:
                    trailers.append(ep_payload)
                    continue

                if ep.content_group:
                    group = entries_by_group.setdefault(ep.content_group, {
                        "content_group": ep.content_group,
                        "title": ep.title,
                        "season_number": season.number,
                        "episode_number": ep.episode_number,
                        "duration_seconds": ep.duration_seconds,
                        "thumbnail_key": thumb.storage_key if thumb else None,
                        "languages": [],
                    })
                    group["languages"].append({"language": ep.language, "episode_id": ep.id})
                    group["languages"].sort(key=lambda x: x["language"])
                else:
                    ungrouped_episodes.append(ep_payload)

        seasons_payload: dict[int, list[dict]] = {}
        for ep_payload in ungrouped_episodes:
            seasons_payload.setdefault(ep_payload["season_number"], []).append(ep_payload)
        for group in entries_by_group.values():
            seasons_payload.setdefault(group["season_number"], []).append(group)

        for season_eps in seasons_payload.values():
            season_eps.sort(key=lambda e: e["episode_number"])

        poster = next((a for a in show.artworks if a.kind == "poster"), None)
        banner = next((a for a in show.artworks if a.kind == "banner"), None)

        show_payload = {
            "id": show.id,
            "title": show.title,
            "synopsis": show.synopsis,
            "category": show.category,
            "poster_key": poster.storage_key if poster else None,
            "banner_key": banner.storage_key if banner else None,
            "seasons": [
                {"season_number": n, "episodes": eps}
                for n, eps in sorted(seasons_payload.items())
            ],
            "trailers": trailers,
        }

        section_name = show.section.value if show.section else "uncategorized"
        sections.setdefault(section_name, []).append(show_payload)

    for shows_list in sections.values():
        shows_list.sort(key=lambda s: s["title"])

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sections": [
            {"section": name, "shows": shows}
            for name, shows in sorted(sections.items())
        ],
        "meta": {"shows_count": len(shows), "episodes_count": episodes_count},
    }, len(shows), episodes_count


def run_publish(db: Session, triggered_by: str) -> PublishRun:
    report = build_validation_report(db)
    if report.blocking_issue_count > 0:
        raise PublishBlockedError(report.blocking_issue_count)

    run = PublishRun(triggered_by=triggered_by, outcome="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        catalogue, shows_count, episodes_count = _build_catalogue_dict(db)
        payload = json.dumps(catalogue, indent=2).encode("utf-8")

        storage = get_storage()
        storage.atomic_write_bytes(CATALOGUE_KEY, payload, content_type="application/json")

        run.outcome = "success"
        run.shows_count = shows_count
        run.episodes_count = episodes_count
        run.catalogue_key = CATALOGUE_KEY
        run.finished_at = datetime.utcnow()
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
    except Exception as exc:  # noqa: BLE001
        run.outcome = "failed"
        run.error = str(exc)
        run.finished_at = datetime.utcnow()
        db.add(run)
        db.commit()
        raise
