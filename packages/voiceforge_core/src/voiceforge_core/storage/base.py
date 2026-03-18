from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class StoredObject:
    bucket: str
    key: str
    content_type: str
    size_bytes: int
    path: Path
    uri: str


class StorageProvider(ABC):
    @abstractmethod
    def put_bytes(self, key: str, payload: bytes, content_type: str) -> StoredObject:
        raise NotImplementedError

    @abstractmethod
    def read_bytes(self, key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def resolve_path(self, key: str) -> Path:
        raise NotImplementedError

