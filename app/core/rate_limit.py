"""Simple in-memory rate limiting for the auth endpoints (login, signup, forgot password).

Each limit counts requests per key (a client IP or an account identifier) in a sliding time window.
Counts live in this process only, so they reset on restart and are not shared between workers;
that is enough for a single uvicorn process. Use a shared store (e.g. Redis) if you run several.

Behind a reverse proxy (nginx, Render, ...) the client IP comes from X-Forwarded-For, which uvicorn
only trusts from the addresses in the FORWARDED_ALLOW_IPS environment variable.
"""
import math
import threading
import time
from collections import deque

from fastapi import HTTPException, Request, status

from app.core.config import settings


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()
        self._calls = 0

    def hit(self, key: str) -> float | None:
        """Record one request for `key`. Returns None if allowed, else seconds until it is allowed again."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            self._calls += 1
            if self._calls % 1000 == 0:
                self._prune(cutoff)

            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= self.max_requests:
                return hits[0] + self.window_seconds - now

            hits.append(now)
            return None

    def _prune(self, cutoff: float) -> None:
        """Drop keys with no recent requests, so memory doesn't grow forever."""
        for key in [k for k, hits in self._hits.items() if not hits or hits[-1] <= cutoff]:
            del self._hits[key]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


MINUTE = 60
HOUR = 60 * MINUTE

# Login: per IP, and per account so guessing one account's password from many IPs is still slow
login_ip_limiter = RateLimiter(max_requests=20, window_seconds=15 * MINUTE)
login_account_limiter = RateLimiter(max_requests=10, window_seconds=15 * MINUTE)

# Forgot password: stops reset emails being used to flood someone's inbox
forgot_ip_limiter = RateLimiter(max_requests=10, window_seconds=HOUR)
forgot_account_limiter = RateLimiter(max_requests=3, window_seconds=HOUR)

# Reset password (token guessing) and signup (mass account creation)
reset_ip_limiter = RateLimiter(max_requests=10, window_seconds=15 * MINUTE)
signup_ip_limiter = RateLimiter(max_requests=10, window_seconds=HOUR)

ALL_LIMITERS = (
    login_ip_limiter,
    login_account_limiter,
    forgot_ip_limiter,
    forgot_account_limiter,
    reset_ip_limiter,
    signup_ip_limiter,
)


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def enforce(limiter: RateLimiter, key: str) -> None:
    """Raise 429 Too Many Requests if `key` is over the limit."""
    if not settings.RATE_LIMIT_ENABLED:
        return
    retry_after = limiter.hit(key)
    if retry_after is not None:
        seconds = max(1, math.ceil(retry_after))
        minutes = math.ceil(seconds / 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many attempts. Please try again in {minutes} minute{'s' if minutes != 1 else ''}.",
            headers={"Retry-After": str(seconds)},
        )


def account_key(identifier: str) -> str:
    return identifier.strip().lower()
