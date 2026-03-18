from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class VoiceProfileStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    TRAINING = "training"
    ACTIVE = "active"
    ARCHIVED = "archived"


class VoiceSampleSource(StrEnum):
    UPLOAD = "upload"
    MICROPHONE = "microphone"
    IMPORT = "import"


class ProcessingStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"


class JobStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConversionMode(StrEnum):
    STUDIO = "studio"
    LIVE = "live"


class EngineBackend(StrEnum):
    SEED_VC = "seed_vc"
    RVC = "rvc"
    OPENVOICE = "openvoice"


class AuditEventType(StrEnum):
    AUTH_REGISTER = "auth_register"
    AUTH_LOGIN = "auth_login"
    VOICE_PROFILE_CREATED = "voice_profile_created"
    VOICE_SAMPLE_UPLOADED = "voice_sample_uploaded"
    TRAINING_JOB_CREATED = "training_job_created"
    TRAINING_JOB_STARTED = "training_job_started"
    TRAINING_JOB_COMPLETED = "training_job_completed"
    TRAINING_JOB_FAILED = "training_job_failed"
    CONVERSION_JOB_CREATED = "conversion_job_created"
    CONVERSION_JOB_STARTED = "conversion_job_started"
    CONVERSION_JOB_COMPLETED = "conversion_job_completed"
    CONVERSION_JOB_FAILED = "conversion_job_failed"
