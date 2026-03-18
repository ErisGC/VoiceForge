from __future__ import annotations

import threading
import time
from collections import defaultdict

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, limit_per_minute: int) -> None:
        super().__init__(app)
        self.limit_per_minute = limit_per_minute
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        with self._lock:
            bucket = [timestamp for timestamp in self._buckets[client_ip] if now - timestamp < 60]
            if len(bucket) >= self.limit_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please retry shortly."},
                )
            bucket.append(now)
            self._buckets[client_ip] = bucket
        return await call_next(request)

