from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import Role, get_current_role
from app.core.db import get_db
from app.models import Episode, PublishStatus, Season, Show
from app.schemas.schemas import EpisodeCreate, EpisodeOut, EpisodeUpdate, SeasonCreate, SeasonOut

router = APIRouter(tags=["episodes"])


@router.post("/admin/seasons", response_model=SeasonOut, status_code=201)
def create_season(payload: SeasonCreate, db: Session = Depends(get_db), role: Role = Depends(get_current_role)):
    if not db.query(Show).filter(Show.id == payload.show_id).first():
        raise HTTPException(404, "Show not found.")
    season = Season(**payload.model_dump())
    db.add(season)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, f"Season {payload.number} already exists for this show.")
    db.refresh(season)
    return season


@router.post("/admin/episodes", response_model=EpisodeOut, status_code=201)
def create_episode(payload: EpisodeCreate, db: Session = Depends(get_db), role: Role = Depends(get_current_role)):
    if not db.query(Season).filter(Season.id == payload.season_id).first():
        raise HTTPException(404, "Season not found.")
    episode = Episode(**payload.model_dump())
    db.add(episode)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409,
            f"An episode with language '{payload.language}' already exists for "
            f"content group '{payload.content_group}'.",
        )
    db.refresh(episode)
    return episode


@router.patch("/admin/episodes/{episode_id}", response_model=EpisodeOut)
def update_episode(episode_id: str, payload: EpisodeUpdate, db: Session = Depends(get_db), role: Role = Depends(get_current_role)):
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(404, "Episode not found.")

    data = payload.model_dump(exclude_unset=True)

    would_be_published = data.get("status", episode.status) == PublishStatus.published.value
    if would_be_published:
        has_duration = data.get("duration_seconds", episode.duration_seconds)
        has_artwork = any(a.kind == "thumbnail" for a in episode.artworks)
        if not has_duration:
            raise HTTPException(422, "Cannot publish an episode without a duration.")
        if not has_artwork:
            raise HTTPException(422, "Cannot publish an episode without artwork (thumbnail).")

    for field, value in data.items():
        setattr(episode, field, value)

    db.add(episode)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "That (content_group, language) combination already exists.")
    db.refresh(episode)
    return episode


@router.delete("/admin/episodes/{episode_id}", status_code=204)
def delete_episode(episode_id: str, db: Session = Depends(get_db), role: Role = Depends(get_current_role)):
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(404, "Episode not found.")
    db.delete(episode)
    db.commit()
