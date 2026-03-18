from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from voiceforge_core.db.models import VoiceProfileFeatureCache
from voiceforge_core.inference.contracts import (
    FeatureCacheArtifact,
    FeatureCacheDescriptor,
    FeatureCacheReference,
    ReferenceAudioCandidate,
)
from voiceforge_core.storage.base import StorageProvider

FEATURE_CACHE_CONTENT_TYPE = "application/octet-stream"


class VoiceProfileFeatureCacheService:
    @staticmethod
    def compute_sample_signature(reference_candidates: tuple[ReferenceAudioCandidate, ...]) -> str:
        normalized = [
            {
                "sample_id": candidate.sample_id,
                "storage_key": candidate.storage_key,
                "waveform_hash": candidate.waveform_hash,
                "filename": candidate.filename,
            }
            for candidate in reference_candidates
        ]
        payload = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def resolve_reference_cache(
        session: Session,
        *,
        storage: StorageProvider,
        voice_profile_id: UUID,
        descriptor: FeatureCacheDescriptor | None,
        reference_candidates: tuple[ReferenceAudioCandidate, ...],
    ) -> FeatureCacheReference | None:
        if descriptor is None or not reference_candidates:
            return None

        sample_signature = VoiceProfileFeatureCacheService.compute_sample_signature(reference_candidates)
        active_cache = session.scalar(
            select(VoiceProfileFeatureCache)
            .where(
                VoiceProfileFeatureCache.voice_profile_id == voice_profile_id,
                VoiceProfileFeatureCache.backend == descriptor.backend,
                VoiceProfileFeatureCache.cache_namespace == descriptor.namespace,
                VoiceProfileFeatureCache.invalidated_at.is_(None),
            )
            .order_by(VoiceProfileFeatureCache.version.desc())
        )
        if active_cache is None:
            return None

        invalidation_reason = VoiceProfileFeatureCacheService._resolve_invalidation_reason(
            active_cache=active_cache,
            descriptor=descriptor,
            sample_signature=sample_signature,
        )
        if invalidation_reason is not None:
            VoiceProfileFeatureCacheService.invalidate_active_caches(
                session,
                voice_profile_id=voice_profile_id,
                backend=descriptor.backend,
                namespace=descriptor.namespace,
                reason=invalidation_reason,
            )
            session.flush()
            return None

        try:
            payload = storage.read_bytes(active_cache.storage_key)
        except OSError:
            active_cache.invalidated_at = datetime.now(timezone.utc)
            active_cache.invalidation_reason = "artifact_missing"
            session.flush()
            return None

        active_cache.last_accessed_at = datetime.now(timezone.utc)
        session.flush()
        return FeatureCacheReference(
            backend=active_cache.backend,
            namespace=active_cache.cache_namespace,
            artifact_version=active_cache.artifact_version,
            cache_format=active_cache.cache_format,
            sample_signature=active_cache.sample_signature,
            config_signature=active_cache.config_signature,
            checksum=active_cache.checksum,
            payload=payload,
            metadata=active_cache.metadata_json or {},
            storage_bucket=active_cache.storage_bucket,
            storage_key=active_cache.storage_key,
        )

    @staticmethod
    def persist_generated_caches(
        session: Session,
        *,
        storage: StorageProvider,
        voice_profile_id: UUID,
        generated_caches: tuple[FeatureCacheArtifact, ...],
    ) -> list[VoiceProfileFeatureCache]:
        persisted: list[VoiceProfileFeatureCache] = []
        for artifact in generated_caches:
            VoiceProfileFeatureCacheService.invalidate_active_caches(
                session,
                voice_profile_id=voice_profile_id,
                backend=artifact.backend,
                namespace=artifact.namespace,
                reason="superseded_by_new_cache",
            )
            version = VoiceProfileFeatureCacheService._next_version(
                session,
                voice_profile_id=voice_profile_id,
                backend=artifact.backend,
                namespace=artifact.namespace,
            )
            storage_key = (
                f"feature-caches/{voice_profile_id}/{artifact.backend.value}/{artifact.namespace}/"
                f"v{version:04d}_{artifact.sample_signature[:12]}_{artifact.config_signature[:12]}.{artifact.cache_format}"
            )
            stored = storage.put_bytes(
                key=storage_key,
                payload=artifact.payload,
                content_type=FEATURE_CACHE_CONTENT_TYPE,
            )
            cache_record = VoiceProfileFeatureCache(
                voice_profile_id=voice_profile_id,
                backend=artifact.backend,
                cache_namespace=artifact.namespace,
                artifact_version=artifact.artifact_version,
                cache_format=artifact.cache_format,
                version=version,
                sample_signature=artifact.sample_signature,
                config_signature=artifact.config_signature,
                storage_bucket=stored.bucket,
                storage_key=stored.key,
                content_type=FEATURE_CACHE_CONTENT_TYPE,
                size_bytes=stored.size_bytes,
                checksum=artifact.checksum,
                metadata_json=artifact.metadata,
                last_accessed_at=datetime.now(timezone.utc),
            )
            session.add(cache_record)
            persisted.append(cache_record)
            session.flush()
        return persisted

    @staticmethod
    def invalidate_active_caches(
        session: Session,
        *,
        voice_profile_id: UUID,
        reason: str,
        backend=None,
        namespace: str | None = None,
    ) -> int:
        statement = select(VoiceProfileFeatureCache).where(
            VoiceProfileFeatureCache.voice_profile_id == voice_profile_id,
            VoiceProfileFeatureCache.invalidated_at.is_(None),
        )
        if backend is not None:
            statement = statement.where(VoiceProfileFeatureCache.backend == backend)
        if namespace is not None:
            statement = statement.where(VoiceProfileFeatureCache.cache_namespace == namespace)

        caches = list(session.scalars(statement))
        if not caches:
            return 0

        invalidated_at = datetime.now(timezone.utc)
        for cache in caches:
            cache.invalidated_at = invalidated_at
            cache.invalidation_reason = reason
        session.flush()
        return len(caches)

    @staticmethod
    def _next_version(
        session: Session,
        *,
        voice_profile_id: UUID,
        backend,
        namespace: str,
    ) -> int:
        current_max = session.scalar(
            select(func.max(VoiceProfileFeatureCache.version)).where(
                VoiceProfileFeatureCache.voice_profile_id == voice_profile_id,
                VoiceProfileFeatureCache.backend == backend,
                VoiceProfileFeatureCache.cache_namespace == namespace,
            )
        )
        return int(current_max or 0) + 1

    @staticmethod
    def _resolve_invalidation_reason(
        *,
        active_cache: VoiceProfileFeatureCache,
        descriptor: FeatureCacheDescriptor,
        sample_signature: str,
    ) -> str | None:
        if active_cache.artifact_version != descriptor.artifact_version:
            return "artifact_version_changed"
        if active_cache.config_signature != descriptor.config_signature:
            return "configuration_changed"
        if active_cache.sample_signature != sample_signature:
            return "voice_samples_changed"
        return None
