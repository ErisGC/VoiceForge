from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.settings import get_settings
from voiceforge_core.modules.auth.service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()


async def _authenticate_ws(token: str | None) -> dict | None:
    """Validate a JWT token and return the decoded payload, or ``None`` on failure.

    Args:
        token: The raw JWT string from the query parameter.

    Returns:
        Decoded JWT payload dict, or ``None`` if the token is missing / invalid.
    """
    if not token:
        return None
    try:
        settings = get_settings()
        return AuthService.decode_access_token(token, settings.jwt_secret)
    except Exception:
        return None


async def _subscribe_redis(user_id: str, websocket: WebSocket) -> None:
    """Subscribe to Redis pub/sub channel for a user's job notifications.

    Listens on ``voiceforge:jobs:{user_id}`` and forwards every message
    to the connected WebSocket client as a JSON text frame.

    Args:
        user_id: The UUID of the authenticated user.
        websocket: The active WebSocket connection.
    """
    try:
        import redis.asyncio as aioredis  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("redis.asyncio not available -- WebSocket will not receive pub/sub events")
        # Keep the connection alive without pub/sub; client can still receive pings.
        try:
            while True:
                await asyncio.sleep(30)
                await websocket.send_json({"type": "ping"})
        except (WebSocketDisconnect, Exception):
            return

    settings = get_settings()
    redis_client = aioredis.from_url(settings.redis_url)
    pubsub = redis_client.pubsub()
    channel = f"voiceforge:jobs:{user_id}"
    await pubsub.subscribe(channel)
    logger.info("WebSocket subscribed to %s", channel)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                try:
                    payload = json.loads(data)
                except (json.JSONDecodeError, TypeError):
                    payload = {"raw": data}
                await websocket.send_json({"type": "job_update", "payload": payload})
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await redis_client.aclose()


@router.websocket("/ws/jobs")
async def websocket_job_notifications(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    """WebSocket endpoint for real-time job status notifications.

    Authenticates the user via a JWT query parameter, then subscribes to
    a Redis pub/sub channel scoped to the user's ID.  Each published
    message is forwarded as a JSON frame.

    Query parameters:
        token: A valid JWT access token.
    """
    payload = await _authenticate_ws(token)
    if payload is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id: str = payload["sub"]
    await websocket.accept()
    logger.info("WebSocket connected for user %s", user_id)

    try:
        await _subscribe_redis(user_id, websocket)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for user %s", user_id)
    except Exception:
        logger.exception("WebSocket error for user %s", user_id)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
