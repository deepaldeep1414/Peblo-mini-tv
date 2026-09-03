from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EpisodeCreate(BaseModel):
    season_id: str
    title: str
    language: str
    content_group: Optional[str] = None
    duration_seconds: Optional[int] = None
    episode_number: int = 1


class EpisodeUpdate(BaseModel):
    title: Optional[str] = None
    language: Optional[str] = None
    content_group: Optional[str] = None
    duration_seconds: Optional[int] = None
    episode_number: Optional[int] = None
    status: Optional[str] = None


class EpisodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    season_id: str
    title: str
    language: str
    content_group: Optional[str]
    duration_seconds: Optional[int]
    episode_number: int
    status: str


class SeasonCreate(BaseModel):
    show_id: str
    number: int


class SeasonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    show_id: str
    number: int
    episodes: list[EpisodeOut] = []


class ShowCreate(BaseModel):
    title: str
    synopsis: str = ""
    category: str = ""
    section: Optional[str] = None


class ShowUpdate(BaseModel):
    title: Optional[str] = None
    synopsis: Optional[str] = None
    category: Optional[str] = None
    section: Optional[str] = None
    status: Optional[str] = None


class ArtworkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    kind: str
    storage_key: str
    width: int
    height: int
    size_bytes: int
    url: str = ""


class ShowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    synopsis: str
    category: str
    section: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    seasons: list[SeasonOut] = []
    artworks: list[ArtworkOut] = []


class ShowListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    category: str
    section: Optional[str]
    status: str


class PaginatedShows(BaseModel):
    items: list[ShowListItem]
    total: int
    page: int
    page_size: int


class ValidationIssue(BaseModel):
    entity_type: str  # "show" | "episode"
    entity_id: str
    entity_label: str
    field: str
    message: str


class ValidationReport(BaseModel):
    generated_at: datetime
    blocking_issue_count: int
    issues_by_show: dict[str, list[ValidationIssue]]


class PublishRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    started_at: datetime
    finished_at: Optional[datetime]
    triggered_by: str
    outcome: str
    shows_count: int
    episodes_count: int
    error: Optional[str]
    catalogue_key: Optional[str]
