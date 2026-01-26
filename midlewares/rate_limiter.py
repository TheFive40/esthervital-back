"""
Rate Limiter using in-memory store (without Redis dependency)
Can be easily migrated to Redis for production
"""

import time
from typing import Dict, Tuple
from datetime import datetime, timedelta
from functools import lru_cache

# In-memory store for rate limiting
# Format: {key: [(timestamp, count), ...]}
_rate_limit_store: Dict[str, list] = {}


class RateLimiter:
    """
    Rate limiter using in-memory storage.
    For production, consider using Redis for distributed systems.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in the time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def is_allowed(self, key: str) -> Tuple[bool, Dict]:
        """
        Check if a request should be allowed.

        Args:
            key: Unique identifier (user_id, IP, email, etc)

        Returns:
            Tuple of (allowed: bool, info: dict with remaining and reset_at)
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Initialize or get existing requests
        if key not in _rate_limit_store:
            _rate_limit_store[key] = []

        # Clean old requests outside the window
        _rate_limit_store[key] = [
            req_time for req_time in _rate_limit_store[key]
            if req_time > window_start
        ]

        current_count = len(_rate_limit_store[key])

        info = {
            "limit": self.max_requests,
            "remaining": max(0, self.max_requests - current_count),
            "reset_at": datetime.fromtimestamp(window_start + self.window_seconds).isoformat(),
            "window_seconds": self.window_seconds
        }

        if current_count < self.max_requests:
            # Request is allowed
            _rate_limit_store[key].append(now)
            info["allowed"] = True
            info["count"] = current_count + 1
            return True, info
        else:
            # Request is denied
            info["allowed"] = False
            info["count"] = current_count
            return False, info

    def reset(self, key: str) -> None:
        """Reset rate limit for a specific key."""
        if key in _rate_limit_store:
            del _rate_limit_store[key]

    def get_status(self, key: str) -> Dict:
        """Get current rate limit status without consuming a request."""
        now = time.time()
        window_start = now - self.window_seconds

        if key not in _rate_limit_store:
            return {
                "limit": self.max_requests,
                "remaining": self.max_requests,
                "count": 0,
                "reset_at": datetime.fromtimestamp(now + self.window_seconds).isoformat()
            }

        # Clean old requests
        _rate_limit_store[key] = [
            req_time for req_time in _rate_limit_store[key]
            if req_time > window_start
        ]

        current_count = len(_rate_limit_store[key])
        return {
            "limit": self.max_requests,
            "remaining": max(0, self.max_requests - current_count),
            "count": current_count,
            "reset_at": datetime.fromtimestamp(window_start + self.window_seconds).isoformat()
        }


# Global rate limiters for different scenarios
GLOBAL_LIMITER = RateLimiter(max_requests=1000, window_seconds=60)  # 1000 req/min globally
AUTH_LIMITER = RateLimiter(max_requests=5, window_seconds=300)  # 5 attempts/5min for auth
USER_LIMITER = RateLimiter(max_requests=100, window_seconds=60)  # 100 req/min per user
IP_LIMITER = RateLimiter(max_requests=500, window_seconds=60)  # 500 req/min per IP
WRITE_LIMITER = RateLimiter(max_requests=50, window_seconds=60)  # 50 writes/min per user