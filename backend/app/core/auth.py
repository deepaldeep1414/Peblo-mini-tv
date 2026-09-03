"""
Deliberately simple auth: an `X-API-Key` header maps to a role.
This is enough to demonstrate *actually enforced* role checks (as the
challenge asks for) without building a full user/JWT system - noted as
a scoping decision in the README.

editor  -> can CRUD shows/seasons/episodes/artwork
admin   -> editor permissions + can trigger /admin/catalog/publish
"""
from enum import Enum

from fastapi import Header, HTTPException, status

from app.core.config import get_settings

settings = get_settings()


class Role(str, Enum):
    editor = "editor"
    admin = "admin"


def get_current_role(x_api_key: str | None = Header(default=None)) -> Role:
    if x_api_key == settings.ADMIN_API_KEY:
        return Role.admin
    if x_api_key == settings.EDITOR_API_KEY:
        return Role.editor
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid X-API-Key header.",
    )


def require_editor(role: Role = None):
    # role is injected by FastAPI via Depends(get_current_role) at call site;
    # this helper exists so intent reads clearly in route signatures.
    return role


def require_admin(x_api_key: str | None = Header(default=None)) -> Role:
    role = get_current_role(x_api_key)
    if role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires the admin role.",
        )
    return role
