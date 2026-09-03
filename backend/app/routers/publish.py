from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import Role, require_admin
from app.core.db import get_db
from app.models import PublishRun
from app.schemas.schemas import PublishRunOut, ValidationReport
from app.services.publish import PublishBlockedError, run_publish
from app.services.validation_report import build_validation_report

router = APIRouter(prefix="/admin", tags=["publish"])


@router.get("/validation-report", response_model=ValidationReport)
def get_validation_report(db: Session = Depends(get_db), role: Role = Depends(require_admin)):
    # Admin-only to match "the viewer UI [never] calling admin endpoints"
    # and keep the report behind the same boundary as publish itself.
    return build_validation_report(db)


@router.post("/catalog/publish", response_model=PublishRunOut, status_code=201)
def publish_catalog(db: Session = Depends(get_db), role: Role = Depends(require_admin)):
    # Only admins may publish -- editors can prep content but not ship it.
    try:
        run = run_publish(db, triggered_by=role.value)
        return run
    except PublishBlockedError as e:
        raise HTTPException(409, f"Publish blocked: {e.issue_count} validation issue(s) must be fixed first.")


@router.get("/catalog/runs", response_model=list[PublishRunOut])
def list_publish_runs(db: Session = Depends(get_db), role: Role = Depends(require_admin)):
    return db.query(PublishRun).order_by(PublishRun.started_at.desc()).limit(50).all()
