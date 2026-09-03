"""
Seeds demo data. Run with: python -m seed.seed  (from /backend, container or venv)

Includes a few DELIBERATELY imperfect rows so the validation report has
something real to surface on first run:
  - "Jungle Buddies" S1E2 is published but has no duration.
  - "Jungle Buddies" S1E3 is published but has no thumbnail.
  - "Story Time" has a published Hindi/English content_group pair (good)
    plus a Season 0 trailer (should not show as a normal season).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import SessionLocal, Base, engine
from app.models import Show, Season, Episode, Section, PublishStatus

Base.metadata.create_all(bind=engine)


def run():
    db = SessionLocal()
    try:
        if db.query(Show).count() > 0:
            print("Seed data already present, skipping.")
            return

        # --- Show 1: fully valid, publishable, with a content_group pair ---
        story_time = Show(
            title="Story Time", synopsis="Bedtime stories from around the world.",
            category="Kids Stories", section=Section.kids, status=PublishStatus.published,
        )
        db.add(story_time)
        db.flush()

        trailer_season = Season(show_id=story_time.id, number=0)
        s1 = Season(show_id=story_time.id, number=1)
        db.add_all([trailer_season, s1])
        db.flush()

        db.add(Episode(
            season_id=trailer_season.id, title="Story Time — Official Trailer",
            language="en", episode_number=1, duration_seconds=45,
            status=PublishStatus.published,
        ))

        db.add(Episode(
            season_id=s1.id, title="The Sleepy Fox", language="en",
            content_group="story-time-s1e1", episode_number=1,
            duration_seconds=420, status=PublishStatus.published,
        ))
        db.add(Episode(
            season_id=s1.id, title="The Sleepy Fox", language="hi",
            content_group="story-time-s1e1", episode_number=1,
            duration_seconds=420, status=PublishStatus.published,
        ))

        # --- Show 2: has deliberate data problems for the validation report ---
        jungle = Show(
            title="Jungle Buddies", synopsis="Animal friends learn to share.",
            category="Kids Comedy", section=Section.kids, status=PublishStatus.published,
        )
        db.add(jungle)
        db.flush()
        j_s1 = Season(show_id=jungle.id, number=1)
        db.add(j_s1)
        db.flush()

        db.add(Episode(
            season_id=j_s1.id, title="New Friends", language="en",
            episode_number=1, duration_seconds=600, status=PublishStatus.published,
        ))
        # imperfect: published but no duration
        db.add(Episode(
            season_id=j_s1.id, title="The Big Storm", language="en",
            episode_number=2, duration_seconds=None, status=PublishStatus.published,
        ))
        # imperfect: published but will have no thumbnail (no artwork added below)
        db.add(Episode(
            season_id=j_s1.id, title="Sharing Day", language="en",
            episode_number=3, duration_seconds=500, status=PublishStatus.published,
        ))

        # --- Show 3: draft, not published, no section yet ---
        draft_show = Show(
            title="Space Explorers (Draft)", synopsis="Coming soon.",
            category="Documentaries", section=None, status=PublishStatus.draft,
        )
        db.add(draft_show)

        db.commit()
        print("Seed complete: 3 shows created (2 published w/ issues, 1 draft).")
        print("Run GET /admin/validation-report to see the surfaced issues.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
