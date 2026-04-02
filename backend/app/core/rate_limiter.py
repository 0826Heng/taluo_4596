from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

from fastapi import HTTPException

from backend.app.core.config import settings


@dataclass
class RateState:
    # key -> timestamps (epoch seconds)
    buckets: dict[tuple[str, str], list[float]]


_state = RateState(buckets=defaultdict(list))


def check_rate_limit(*, user_id: str, path: str) -> None:
    now = time.time()
    key = (user_id, path)

    window_start = now - 60.0
    timestamps = _state.buckets[key]
    # 清理窗口外的请求
    _state.buckets[key] = [t for t in timestamps if t >= window_start]
    timestamps = _state.buckets[key]

    if len(timestamps) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="rate_limited")

    timestamps.append(now)

