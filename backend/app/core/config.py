"""
Central settings, loaded from environment variables (.env in dev).
Port defaults are intentionally NON-standard per project requirements:
  Postgres  -> 55432 (default is 5432)
  Backend   -> 8088   (default is 8000)
"""
import os
from functools import lru_cache


class Settings:
    # --- App ---
    APP_NAME: str = "Peblo TV Mini API"
    ENV: str = os.getenv("ENV", "development")
    API_PORT: int = int(os.getenv("API_PORT", "8088"))

    # --- Database ---
    # Falls back to a local sqlite file so `pytest` / quick local runs
    # don't require Postgres. docker-compose always sets DATABASE_URL
    # to the Postgres DSN below.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://peblo:peblo@localhost:55432/peblo_tv_mini",
    )

    # --- Auth (deliberately simple: static API-key -> role mapping) ---
    # In production this would be replaced by real JWT/OAuth; see README
    # Part E for the trade-off discussion.
    EDITOR_API_KEY: str = os.getenv("EDITOR_API_KEY", "editor-key-change-me")
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "admin-key-change-me")

    # --- Storage ---
    # "local" -> disk under STORAGE_ROOT. "s3" -> any S3-compatible
    # endpoint (R2, MinIO) via STORAGE_* vars below. Swapping backends
    # is a one-line change (STORAGE_BACKEND) because both implement the
    # same StorageBackend interface — see app/storage/base.py.
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")
    STORAGE_ROOT: str = os.getenv("STORAGE_ROOT", "/data/storage")

    STORAGE_S3_ENDPOINT: str = os.getenv("STORAGE_S3_ENDPOINT", "")
    STORAGE_S3_BUCKET: str = os.getenv("STORAGE_S3_BUCKET", "peblo-tv-mini")
    STORAGE_S3_ACCESS_KEY: str = os.getenv("STORAGE_S3_ACCESS_KEY", "")
    STORAGE_S3_SECRET_KEY: str = os.getenv("STORAGE_S3_SECRET_KEY", "")
    STORAGE_S3_REGION: str = os.getenv("STORAGE_S3_REGION", "auto")

    # --- Artwork validation (from reference.json conventions) ---
    ARTWORK_MAX_BYTES: int = 200 * 1024  # 200 KB ceiling
    ARTWORK_SPECS = {
        "poster": {"ratio": (2, 3), "target": (600, 900)},
        "banner": {"ratio": (16, 9), "target": (1280, 720)},
        "thumbnail": {"ratio": (16, 9), "target": (640, 360)},
    }
    ARTWORK_RATIO_TOLERANCE: float = 0.02  # 2% slack on aspect ratio checks

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5180,http://localhost:5190",
    ).split(",")


@lru_cache
def get_settings() -> Settings:
    return Settings()
