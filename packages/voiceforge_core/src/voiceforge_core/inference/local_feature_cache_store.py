from __future__ import annotations

import hashlib
import json
from pathlib import Path

from voiceforge_core.inference.contracts import FeatureCacheArtifact, FeatureCacheDescriptor, FeatureCacheReference


class LocalFeatureCacheStore:
    """Filesystem-backed cache store for reusable backend-specific feature artifacts."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()

    def resolve(
        self,
        *,
        descriptor: FeatureCacheDescriptor,
        sample_signature: str,
    ) -> FeatureCacheReference | None:
        artifact_path = self._artifact_path(
            backend=descriptor.backend.value,
            namespace=descriptor.namespace,
            artifact_version=descriptor.artifact_version,
            cache_format=descriptor.cache_format,
            sample_signature=sample_signature,
            config_signature=descriptor.config_signature,
        )
        manifest_path = self._manifest_path(artifact_path)
        if not artifact_path.exists() or not manifest_path.exists():
            return None

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload = artifact_path.read_bytes()
        except (OSError, json.JSONDecodeError):
            return None

        checksum = hashlib.sha256(payload).hexdigest()
        if checksum != manifest.get("checksum"):
            return None
        if manifest.get("sample_signature") != sample_signature:
            return None
        if manifest.get("config_signature") != descriptor.config_signature:
            return None
        if manifest.get("artifact_version") != descriptor.artifact_version:
            return None

        return FeatureCacheReference(
            backend=descriptor.backend,
            namespace=descriptor.namespace,
            artifact_version=descriptor.artifact_version,
            cache_format=descriptor.cache_format,
            sample_signature=sample_signature,
            config_signature=descriptor.config_signature,
            checksum=checksum,
            payload=payload,
            metadata=manifest.get("metadata") or {},
            storage_bucket=None,
            storage_key=str(artifact_path),
        )

    def persist(self, artifact: FeatureCacheArtifact) -> FeatureCacheReference:
        artifact_path = self._artifact_path(
            backend=artifact.backend.value,
            namespace=artifact.namespace,
            artifact_version=artifact.artifact_version,
            cache_format=artifact.cache_format,
            sample_signature=artifact.sample_signature,
            config_signature=artifact.config_signature,
        )
        manifest_path = self._manifest_path(artifact_path)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_bytes(artifact.payload)
        manifest_path.write_text(
            json.dumps(
                {
                    "backend": artifact.backend.value,
                    "namespace": artifact.namespace,
                    "artifact_version": artifact.artifact_version,
                    "cache_format": artifact.cache_format,
                    "sample_signature": artifact.sample_signature,
                    "config_signature": artifact.config_signature,
                    "checksum": artifact.checksum,
                    "metadata": artifact.metadata,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return FeatureCacheReference(
            backend=artifact.backend,
            namespace=artifact.namespace,
            artifact_version=artifact.artifact_version,
            cache_format=artifact.cache_format,
            sample_signature=artifact.sample_signature,
            config_signature=artifact.config_signature,
            checksum=artifact.checksum,
            payload=artifact.payload,
            metadata=artifact.metadata,
            storage_bucket=None,
            storage_key=str(artifact_path),
        )

    def delete_namespace(self, *, backend: str, namespace: str) -> None:
        namespace_path = self.root / backend / namespace
        if not namespace_path.exists():
            return
        for child in sorted(namespace_path.rglob("*"), reverse=True):
            try:
                if child.is_file():
                    child.unlink()
                else:
                    child.rmdir()
            except OSError:
                continue
        try:
            namespace_path.rmdir()
        except OSError:
            pass

    def _artifact_path(
        self,
        *,
        backend: str,
        namespace: str,
        artifact_version: str,
        cache_format: str,
        sample_signature: str,
        config_signature: str,
    ) -> Path:
        return (
            self.root
            / backend
            / namespace
            / artifact_version
            / sample_signature[:2]
            / f"{sample_signature}_{config_signature[:16]}.{cache_format}"
        )

    @staticmethod
    def _manifest_path(artifact_path: Path) -> Path:
        return artifact_path.with_suffix(f"{artifact_path.suffix}.json")
