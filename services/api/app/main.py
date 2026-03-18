from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.dependencies import get_runtime
from app.middleware.rate_limit import RateLimitMiddleware
from app.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_runtime()
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="VoiceForge production-ready starter backend for cross-platform voice conversion.",
    lifespan=lifespan,
)
app.add_middleware(RateLimitMiddleware, limit_per_minute=settings.rate_limit_per_minute)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
