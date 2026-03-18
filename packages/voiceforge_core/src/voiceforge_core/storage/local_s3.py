from __future__ import annotations

from pathlib import Path

from voiceforge_core.storage.base import StorageProvider, StoredObject


class LocalS3CompatibleStorage(StorageProvider):
    def __init__(self, root: str, bucket: str) -> None:
        self.root = Path(root).expanduser().resolve()
        self.bucket = bucket
        self.bucket_path = self.root / bucket
        self.bucket_path.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, key: str, payload: bytes, content_type: str) -> StoredObject:
        file_path = self.bucket_path / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(payload)
        return StoredObject(
            bucket=self.bucket,
            key=key,
            content_type=content_type,
            size_bytes=len(payload),
            path=file_path,
            uri=f"s3://{self.bucket}/{key}",
        )

    def read_bytes(self, key: str) -> bytes:
        return self.resolve_path(key).read_bytes()

    def resolve_path(self, key: str) -> Path:
        return self.bucket_path / key

