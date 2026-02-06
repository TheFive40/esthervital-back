"""
Rate Limiter implementation for API protection
Implements sliding window rate limiting for different operation types
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from collections import defaultdict
import threading


class RateLimiter:
    """
    Thread-safe sliding window rate limiter
    """
    
    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
    
    def is_allowed(self, identifier: str) -> Tuple[bool, Dict]:
        """
        Check if a request is allowed for the given identifier
        
        Args:
            identifier: Unique identifier for the rate limit (e.g., user_id, IP)
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        with self._lock:
            # Clean old requests outside the window
            self._requests[identifier] = [
                req_time for req_time in self._requests[identifier]
                if req_time > window_start
            ]
            
            current_count = len(self._requests[identifier])
            remaining = max(0, self.max_requests - current_count)
            reset_at = (now + timedelta(seconds=self.window_seconds)).isoformat()
            
            info = {
                "limit": self.max_requests,
                "remaining": remaining,
                "reset_at": reset_at,
                "window_seconds": self.window_seconds
            }
            
            if current_count >= self.max_requests:
                return False, info
            
            # Add current request
            self._requests[identifier].append(now)
            info["remaining"] = remaining - 1
            
            return True, info
    
    def reset(self, identifier: str) -> None:
        """
        Reset rate limit for a specific identifier
        """
        with self._lock:
            self._requests[identifier] = []
    
    def get_status(self, identifier: str) -> Dict:
        """
        Get current rate limit status without counting a request
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        with self._lock:
            valid_requests = [
                req_time for req_time in self._requests[identifier]
                if req_time > window_start
            ]
            
            current_count = len(valid_requests)
            remaining = max(0, self.max_requests - current_count)
            reset_at = (now + timedelta(seconds=self.window_seconds)).isoformat()
            
            return {
                "limit": self.max_requests,
                "used": current_count,
                "remaining": remaining,
                "reset_at": reset_at,
                "window_seconds": self.window_seconds
            }


# Pre-configured rate limiters for different use cases

# Authentication attempts: 5 per minute (stricter to prevent brute force)
AUTH_LIMITER = RateLimiter(max_requests=5, window_seconds=60)

# General user requests: 100 per minute
USER_LIMITER = RateLimiter(max_requests=100, window_seconds=60)

# Write operations (POST, PUT, DELETE): 30 per minute
WRITE_LIMITER = RateLimiter(max_requests=30, window_seconds=60)

# API endpoints: 1000 per minute (for general API access)
API_LIMITER = RateLimiter(max_requests=1000, window_seconds=60)

# Global rate limiter: 2000 requests per minute across all users
GLOBAL_LIMITER = RateLimiter(max_requests=2000, window_seconds=60)

# IP-based rate limiter: 500 requests per minute per IP
IP_LIMITER = RateLimiter(max_requests=500, window_seconds=60)
