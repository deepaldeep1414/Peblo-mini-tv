import os
from pathlib import Path

from app.storage.base import StorageBackend


class LocalDiskStorage(StorageBackend):
    """
    Local-disk implementation. Atomicity is achieved the standard POSIX
    way: write to a temp file in the same directory (so it's on the same
    filesystem/mount), fsync it, then os.replace() it over the target
    path. os.replace is atomic on POSIX and Windows -- a concurrent
    reader either sees the old complete file or the new complete file,
    never a partial one.
    """

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        p = (self.root / key).resolve()
        if self.root.resolve() not in p.parents and p != self.root.resolve():
            raise ValueError("Invalid storage key (path traversal).")
        return p

    def write_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    def read_bytes(self, key: str) -> bytes:
        with open(self._path(key), "rb") as f:
            return f.read()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def atomic_write_bytes(self, key: str, data: bytes, content_type: str = "application/json") -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
        with open(tmp_path, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)  # atomic on POSIX + Windows

    def url_for(self, key: str) -> str:
        return f"/static/{key}"
