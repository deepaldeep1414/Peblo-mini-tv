"""
OPTIONAL demo helper. Run this AFTER seed.seed has run, to patch the
deliberately-imperfect seed data with placeholder artwork (and one missing
duration) so the catalogue can actually be published end-to-end.

This is intentionally a SEPARATE script from seed.py: seed.py's job is to
demonstrate the validation report catching real problems (see the
Publish tab -- it should show 11 blocking issues on a fresh install).
Run this script only once you've looked at that and want to see the
rest of the flow (a green Publish + a populated Viewer).

Usage (from repo root, container running):
    docker-compose exec api python -m seed.fix_demo_data

Or locally (from /backend, venv active):
    python -m seed.fix_demo_data
"""
import sys
import os
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw

from app.core.db import SessionLocal
from app.models import Show, Episode, Artwork, ArtworkKind
from app.storage import get_storage

SPECS = {
    ArtworkKind.poster: (600, 900, (76, 29, 149)),      # violet
    ArtworkKind.banner: (1280, 720, (14, 116, 144)),    # teal
    ArtworkKind.thumbnail: (640, 360, (190, 24, 93)),   # pink
}


def _make_placeholder(kind: ArtworkKind, label: str) -> bytes:
    width, height, color = SPECS[kind]
    img = Image.new("RGB", (width, height), color=color)
    draw = ImageDraw.Draw(img)
    text = f"{label}\n{kind.value}\n{width}x{height}"
    draw.multiline_text((20, 20), text, fill=(255, 255, 255), spacing=6)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return buf.getvalue()


def _add_artwork(db, storage, kind: ArtworkKind, label: str, *, show_id=None, episode_id=None):
    data = _make_placeholder(kind, label)
    owner = show_id or episode_id
    key = f"artwork/{owner}/{kind.value}-placeholder.jpg"
    storage.write_bytes(key, data, content_type="image/jpeg")
    width, height, _ = SPECS[kind]
    db.add(Artwork(
        kind=kind, storage_key=key, width=width, height=height, size_bytes=len(data),
        show_id=show_id, episode_id=episode_id,
    ))


def run():
    db = SessionLocal()
    storage = get_storage()
    try:
        added_artwork = 0
        fixed_durations = 0

        shows = db.query(Show).all()
        for show in shows:
            existing_kinds = {a.kind for a in show.artworks}
            if ArtworkKind.poster not in existing_kinds:
                _add_artwork(db, storage, ArtworkKind.poster, show.title, show_id=show.id)
                added_artwork += 1
            if ArtworkKind.banner not in existing_kinds:
                _add_artwork(db, storage, ArtworkKind.banner, show.title, show_id=show.id)
                added_artwork += 1

            for season in show.seasons:
                for ep in season.episodes:
                    ep_existing = {a.kind for a in ep.artworks}
                    if ArtworkKind.thumbnail not in ep_existing:
                        _add_artwork(db, storage, ArtworkKind.thumbnail, ep.title, episode_id=ep.id)
                        added_artwork += 1
                    if ep.status.value == "published" and not ep.duration_seconds:
                        ep.duration_seconds = 540  # placeholder: 9 min
                        db.add(ep)
                        fixed_durations += 1

        db.commit()
        print(f"Added {added_artwork} placeholder artwork file(s).")
        print(f"Filled {fixed_durations} missing duration(s).")
        print("Done. Open the CMS Publish tab -- blocking issues should now be 0.")
        print("Click 'Publish catalogue', then reload the Viewer.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
