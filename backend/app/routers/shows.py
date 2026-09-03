from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.auth import Role, get_current_role
from app.core.db import get_db
from app.models import PublishStatus, Section, Show
from app.schemas.schemas import PaginatedShows, ShowCreate, ShowOut, ShowUpdate

router = APIRouter(prefix="/admin/shows", tags=["shows"])


@router.get("", response_model=PaginatedShows)
def list_shows(
    q: str | None = None,
    section: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    role: Role = Depends(get_current_role),  # editor or admin may read
):
    query = db.query(Show)
    if q:
        query = query.filter(Show.title.ilike(f"%{q}%"))
    if section:
        query = query.filter(Show.section == section)
    if status_filter:
        query = query.filter(Show.status == status_filter)

    total = query.count()
    items = (
        query.order_by(Show.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedShows(items=items, total=total, page=page, page_size=page_size)


@router.get("/{show_id}", response_model=ShowOut)
def get_show(show_id: str, db: Session = Depends(get_db), role: Role = Depends(get_current_role)):
    show = db.query(Show).options(
        joinedload(Show.seasons), joinedload(Show.artworks)
    ).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(404, "Show not found.")
    return show


@router.post("", response_model=ShowOut, status_code=201)
def create_show(payload: ShowCreate, db: Session = Depends(get_db), role: Role = Depends(get_current_role)):
    if payload.section and payload.section not in Section.__members__:
        raise HTTPException(422, f"Invalid section '{payload.section}'.")
    show = Show(**payload.model_dump())
    db.add(show)
    db.commit()
    db.refresh(show)
    return show


@router.patch("/{show_id}", response_model=ShowOut)
def update_show(show_id: str, payload: ShowUpdate, db: Session = Depends(get_db), role: Role = Depends(get_current_role)):
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(404, "Show not found.")

    data = payload.model_dump(exclude_unset=True)

    if "status" in data and data["status"] == PublishStatus.published.value:
        if not show.section and "section" not in data:
            raise HTTPException(422, "A published show must have a section assigned.")

    for field, value in data.items():
        setattr(show, field, value)

    db.add(show)
    db.commit()
    db.refresh(show)
    return show


@router.delete("/{show_id}", status_code=204)
def delete_show(show_id: str, db: Session = Depends(get_db), role: Role = Depends(get_current_role)):
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(404, "Show not found.")
    db.delete(show)
    db.commit()
