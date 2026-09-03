from functools import lru_cache

from app.core.config import get_settings
from app.storage.base import StorageBackend
from app.storage.local import LocalDiskStorage


@lru_cache
def get_storage() -> StorageBackend:
    settings = get_settings()
    if settings.STORAGE_BACKEND == "s3":
        from app.storage.s3_compatible import S3CompatibleStorage
        return S3CompatibleStorage(
            endpoint=settings.STORAGE_S3_ENDPOINT,
            bucket=settings.STORAGE_S3_BUCKET,
            access_key=settings.STORAGE_S3_ACCESS_KEY,
            secret_key=settings.STORAGE_S3_SECRET_KEY,
            region=settings.STORAGE_S3_REGION,
        )
    return LocalDiskStorage(settings.STORAGE_ROOT)
