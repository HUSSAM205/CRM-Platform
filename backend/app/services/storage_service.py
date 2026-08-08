from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from functools import lru_cache
from pathlib import Path

import aiofiles

from app.core.config import get_settings


class StorageService(ABC):
    @abstractmethod
    async def put(self, key: str, data: bytes) -> None: ...

    @abstractmethod
    def get_stream(self, key: str) -> AsyncIterator[bytes]: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...


class LocalStorageService(StorageService):
    """Dev-only filesystem adapter behind the same interface an S3 adapter would use.

    Swapping to real S3/R2 in production is a config change (STORAGE_BACKEND=s3), not a
    code change at call sites — see get_storage_service().
    """

    def __init__(self, base_path: str) -> None:
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        path = (self.base_path / key).resolve()
        if self.base_path not in path.parents and path != self.base_path:
            raise ValueError("Invalid storage key")
        return path

    async def put(self, key: str, data: bytes) -> None:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            await f.write(data)

    async def get_stream(self, key: str) -> AsyncIterator[bytes]:
        path = self._resolve(key)
        async with aiofiles.open(path, "rb") as f:
            while chunk := await f.read(1024 * 1024):
                yield chunk

    async def delete(self, key: str) -> None:
        self._resolve(key).unlink(missing_ok=True)


@lru_cache
def get_storage_service() -> StorageService:
    settings = get_settings()
    if settings.storage_backend == "local":
        return LocalStorageService(settings.local_storage_path)
    raise NotImplementedError(
        f"Storage backend '{settings.storage_backend}' has no adapter yet — add an S3-compatible "
        "implementation of StorageService here when deploying to a real S3/R2 bucket."
    )
