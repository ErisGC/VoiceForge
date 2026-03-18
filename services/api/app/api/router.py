from fastapi import APIRouter

from app.api.routes import audit, auth, conversion_jobs, health, subscriptions, training_jobs, users, voice_profiles

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(voice_profiles.router, prefix="/voice-profiles", tags=["voice_profiles"])
api_router.include_router(training_jobs.router, prefix="/training-jobs", tags=["training_jobs"])
api_router.include_router(conversion_jobs.router, prefix="/conversion-jobs", tags=["conversion_jobs"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["audit"])

