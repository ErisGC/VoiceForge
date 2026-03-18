from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from redis import Redis


@dataclass(slots=True)
class JobEnvelope:
    job_type: str
    payload: dict
    enqueued_at: str


class RedisJobQueue:
    def __init__(self, redis_url: str, queue_name: str) -> None:
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.queue_name = queue_name

    def enqueue(self, job_type: str, payload: dict) -> None:
        envelope = JobEnvelope(
            job_type=job_type,
            payload=payload,
            enqueued_at=datetime.now(timezone.utc).isoformat(),
        )
        self.redis.lpush(self.queue_name, json.dumps(envelope.__dict__))

    def dequeue(self, timeout: int = 5) -> JobEnvelope | None:
        item = self.redis.brpop(self.queue_name, timeout=timeout)
        if item is None:
            return None
        _, raw_payload = item
        data = json.loads(raw_payload)
        return JobEnvelope(**data)

