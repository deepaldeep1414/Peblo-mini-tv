"""
Storage abstraction. Swapping local disk <-> S3-compatible (Cloudflare R2,
MinIO) is a one-class change: implement StorageBackend and flip
STORAGE_BACKEND in the environment. Nothing above this layer (routers,
services) knows or cares which one is active.
"""
from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def write_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        ...

    @abstractmethod
    def read_bytes(self, key: str) -> bytes:
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        ...

    @abstractmethod
    def atomic_write_bytes(self, key: str, data: bytes, content_type: str = "application/json") -> None:
        """
        Write `data` such that readers NEVER observe a partially-written
        file at `key`: write to a temp/staging key, then perform a single
        atomic rename/copy-then-delete into place. Used for catalogue.json.
        """
        ...

    @abstractmethod
    def url_for(self, key: str) -> str:
        ...
