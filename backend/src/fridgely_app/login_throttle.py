"""Bounded, thread-safe login windows for the deployed single-worker host."""
from collections import deque
from math import ceil
from threading import Lock

from fastapi import HTTPException


class LoginThrottle:
    def __init__(self, clock, window_seconds=60, account_limit=5, source_limit=200, max_buckets=10000):
        self.clock, self.window = clock, window_seconds
        self.account_limit, self.source_limit = account_limit, source_limit
        self.max_buckets = max_buckets
        self._buckets, self._lock = {}, Lock()

    def reserve(self, source, email):
        """Reserve before expensive password work, including concurrent requests."""
        with self._lock:
            now = self.clock().timestamp()
            for key, events in list(self._buckets.items()):
                while events and events[0] <= now - self.window:
                    events.popleft()
                if not events:
                    del self._buckets[key]
            keys = [(('source', source), self.source_limit), (('account', source, email), self.account_limit)]
            retry = max((ceil(self.window - (now - self._buckets[key][0]))
                         for key, limit in keys if len(self._buckets.get(key, ())) >= limit), default=0)
            if retry or len(self._buckets) + sum(key not in self._buckets for key, _ in keys) > self.max_buckets:
                raise HTTPException(429, headers={'Retry-After': str(max(1, retry or self.window))})
            for key, _limit in keys:
                self._buckets.setdefault(key, deque()).append(now)

    def succeeded(self, source, email):
        with self._lock:
            self._buckets.pop(('account', source, email), None)
