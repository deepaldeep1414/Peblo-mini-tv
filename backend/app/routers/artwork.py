import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import Role, get_current_role
from app.core.db import get_db
from app.models import Artwork, Episode, Show
from app.schemas.schemas import ArtworkOut
from app.services.artwork_validation import ArtworkValidationError, validate_and_probe
from app.storage import get_storage

router = APIRouter(prefix="/admin/artwork", tags=["artwork"])


@router.post("", response_model=ArtworkOut, status_code=201)
async def upload_artwork(
    kind: str = Form(...),
    show_id: str | None = Form(default=None),
    episode_id: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    role: Role = Depends(get_current_role),
):
    if bool(show_id) == bool(episode_id):
        raise HTTPException(422, "Provide exactly one of show_id or episode_id.")

    if show_id and not db.query(Show).filter(Show.id == show_id).first():
        raise HTTPException(404, "Show not found.")
    if episode_id and not db.query(Episode).filter(Episode.id == episode_id).first():
        raise HTTPException(404, "Episode not found.")

    data = await file.read()

    try:
        width, height = validate_and_probe(kind, data)
    except ArtworkValidationError as e:
        raise HTTPException(422, str(e))

    ext = (file.filename or "image").rsplit(".", 1)[-1].lower()
    owner = show_id or episode_id
    key = f"artwork/{owner}/{kind}-{uuid.uuid4().hex[:8]}.{ext}"

    storage = get_storage()
    storage.write_bytes(key, data, content_type=file.content_type or "image/jpeg")

    artwork = Artwork(
        kind=kind, storage_key=key, width=width, height=height,
        size_bytes=len(data), show_id=show_id, episode_id=episode_id,
    )
    db.add(artwork)
    db.commit()
    db.refresh(artwork)

    out = ArtworkOut.model_validate(artwork)
    out.url = storage.url_for(key)
    return out
