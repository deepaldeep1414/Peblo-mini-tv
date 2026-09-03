import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from app.core.db import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Section(str, enum.Enum):
    kids = "kids"
    family = "family"
    originals = "originals"
    documentaries = "documentaries"
    movies = "movies"


class PublishStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class Show(Base):
    __tablename__ = "shows"

    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String, nullable=False)
    synopsis = Column(Text, default="")
    category = Column(String, default="")
    section = Column(SAEnum(Section), nullable=True)  # required only to publish
    status = Column(SAEnum(PublishStatus), default=PublishStatus.draft, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    seasons = relationship("Season", back_populates="show", cascade="all, delete-orphan")
    artworks = relationship("Artwork", back_populates="show", cascade="all, delete-orphan")


class Season(Base):
    __tablename__ = "seasons"

    id = Column(String, primary_key=True, default=gen_uuid)
    show_id = Column(String, ForeignKey("shows.id"), nullable=False)
    number = Column(Integer, nullable=False)  # 0 == trailers, per reference.json convention

    show = relationship("Show", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("show_id", "number", name="uq_show_season_number"),)


class Episode(Base):
    __tablename__ = "episodes"

    id = Column(String, primary_key=True, default=gen_uuid)
    season_id = Column(String, ForeignKey("seasons.id"), nullable=False)
    title = Column(String, nullable=False)
    language = Column(String, nullable=False)  # e.g. "en", "hi"
    content_group = Column(String, nullable=True)  # variants sharing this collapse in catalogue
    duration_seconds = Column(Integer, nullable=True)
    episode_number = Column(Integer, nullable=False, default=1)
    status = Column(SAEnum(PublishStatus), default=PublishStatus.draft, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    season = relationship("Season", back_populates="episodes")
    artworks = relationship("Artwork", back_populates="episode", cascade="all, delete-orphan")

    __table_args__ = (
        # (content_group, language) must be unique -- but only enforced when
        # content_group is set (NULLs are exempt in Postgres/SQLite unique
        # indexes, so this direct constraint is sufficient in practice).
        UniqueConstraint("content_group", "language", name="uq_content_group_language"),
    )


class ArtworkKind(str, enum.Enum):
    poster = "poster"
    banner = "banner"
    thumbnail = "thumbnail"


class Artwork(Base):
    __tablename__ = "artworks"

    id = Column(String, primary_key=True, default=gen_uuid)
    kind = Column(SAEnum(ArtworkKind), nullable=False)
    storage_key = Column(String, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # An artwork belongs to either a show (hero/poster at show level) or an
    # episode (thumbnail); exactly one of these is set.
    show_id = Column(String, ForeignKey("shows.id"), nullable=True)
    episode_id = Column(String, ForeignKey("episodes.id"), nullable=True)

    show = relationship("Show", back_populates="artworks")
    episode = relationship("Episode", back_populates="artworks")


class PublishRun(Base):
    __tablename__ = "publish_runs"

    id = Column(String, primary_key=True, default=gen_uuid)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    triggered_by = Column(String, nullable=False)  # role/user identifier
    outcome = Column(String, nullable=False, default="running")  # running|success|failed
    shows_count = Column(Integer, default=0)
    episodes_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    catalogue_key = Column(String, nullable=True)  # storage key of the file this run wrote
    extra = Column(JSON, default=dict)
