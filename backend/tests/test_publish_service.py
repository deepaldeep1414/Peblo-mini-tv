from app.core.db import SessionLocal, Base
from app.models import Show, Season, Episode, Artwork, ArtworkKind, Section, PublishStatus
from app.services.publish import _build_catalogue_dict


def _make_published_episode(db, season, title, language, content_group=None, episode_number=1):
    ep = Episode(
        season_id=season.id, title=title, language=language, content_group=content_group,
        episode_number=episode_number, duration_seconds=300, status=PublishStatus.published,
    )
    db.add(ep)
    db.flush()
    db.add(Artwork(kind=ArtworkKind.thumbnail, storage_key=f"thumb-{ep.id}", width=640, height=360,
                    size_bytes=1000, episode_id=ep.id))
    return ep


def test_season_zero_becomes_trailers_not_a_normal_season(db_session):
    db = db_session
    show = Show(title="A Show", section=Section.kids, status=PublishStatus.published)
    db.add(show)
    db.flush()
    db.add(Artwork(kind=ArtworkKind.poster, storage_key="p", width=600, height=900, size_bytes=1, show_id=show.id))
    db.add(Artwork(kind=ArtworkKind.banner, storage_key="b", width=1280, height=720, size_bytes=1, show_id=show.id))

    trailer_season = Season(show_id=show.id, number=0)
    real_season = Season(show_id=show.id, number=1)
    db.add_all([trailer_season, real_season])
    db.flush()

    _make_published_episode(db, trailer_season, "Trailer", "en")
    _make_published_episode(db, real_season, "Ep 1", "en")
    db.commit()

    catalogue, shows_count, episodes_count = _build_catalogue_dict(db)

    show_payload = catalogue["sections"][0]["shows"][0]
    season_numbers = [s["season_number"] for s in show_payload["seasons"]]
    assert 0 not in season_numbers
    assert len(show_payload["trailers"]) == 1
    assert episodes_count == 2


def test_content_group_collapses_language_variants(db_session):
    db = db_session
    show = Show(title="Lang Show", section=Section.kids, status=PublishStatus.published)
    db.add(show)
    db.flush()
    db.add(Artwork(kind=ArtworkKind.poster, storage_key="p", width=600, height=900, size_bytes=1, show_id=show.id))
    db.add(Artwork(kind=ArtworkKind.banner, storage_key="b", width=1280, height=720, size_bytes=1, show_id=show.id))

    season = Season(show_id=show.id, number=1)
    db.add(season)
    db.flush()

    _make_published_episode(db, season, "Shared Ep", "en", content_group="g1")
    _make_published_episode(db, season, "Shared Ep", "hi", content_group="g1")
    db.commit()

    catalogue, _, _ = _build_catalogue_dict(db)
    show_payload = catalogue["sections"][0]["shows"][0]
    all_eps = [e for s in show_payload["seasons"] for e in s["episodes"]]

    assert len(all_eps) == 1  # collapsed into one entry
    assert sorted(l["language"] for l in all_eps[0]["languages"]) == ["en", "hi"]
