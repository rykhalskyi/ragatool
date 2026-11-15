import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict


class SlidingWindowRateLimiter:
    """Thread-safe in-memory limiter used for login throttling."""

    def __init__(self, max_events: int, window_seconds: float) -> None:
        self._max_events = max(1, max_events)
        self._window = max(1.0, float(window_seconds))
        self._events: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def consume(self, key: str) -> int:
        """Record an attempt. Returns 0 when allowed, else a Retry-After delay."""
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            if len(self._events) > 10000:
                self._events.clear()
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self._max_events:
                retry_after = int(self._window - (now - events[0])) + 1
                return max(retry_after, 1)
            events.append(now)
            return 0

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
