"""Unified rate limiting component for the Entity framework."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional


class RateLimitAlgorithm(Enum):
    """Available rate limiting algorithms."""

    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    max_requests: int
    time_window: float  # in seconds
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    burst_size: Optional[int] = None  # For token bucket
    leak_rate: Optional[float] = None  # For leaky bucket


class RateLimiter:
    """Unified rate limiter with multiple algorithm support."""

    def __init__(
        self,
        max_requests: int,
        time_window: float = 60.0,
        algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW,
        burst_size: Optional[int] = None,
        leak_rate: Optional[float] = None,
    ):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds (default 60)
            algorithm: Rate limiting algorithm to use
            burst_size: Maximum burst size for token bucket
            leak_rate: Leak rate for leaky bucket (requests per second)
        """
        self.config = RateLimitConfig(
            max_requests=max_requests,
            time_window=time_window,
            algorithm=algorithm,
            burst_size=burst_size or max_requests,
            leak_rate=leak_rate or (max_requests / time_window),
        )

        # Algorithm-specific storage
        self._requests: deque = deque()  # For sliding window
        self._window_start: float = time.time()  # For fixed window
        self._window_count: int = 0  # For fixed window
        self._tokens: float = float(
            self.config.burst_size or max_requests
        )  # For token bucket
        self._last_update: float = time.time()  # For token/leaky bucket
        self._bucket_level: float = 0.0  # For leaky bucket

        # Thread safety
        self._lock = asyncio.Lock()
        self._sync_lock = None  # Will be created if needed

        # Metrics
        self._metrics = {
            "total_requests": 0,
            "allowed_requests": 0,
            "denied_requests": 0,
            "last_denied_time": None,
        }

    async def allow_request(self, identifier: Optional[str] = None) -> bool:
        """Check if request is allowed under rate limit.

        Args:
            identifier: Optional identifier for per-key rate limiting

        Returns:
            True if request is allowed, False otherwise
        """
        async with self._lock:
            self._metrics["total_requests"] += 1

            if self.config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                allowed = self._check_sliding_window()
            elif self.config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                allowed = self._check_token_bucket()
            elif self.config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
                allowed = self._check_fixed_window()
            elif self.config.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
                allowed = self._check_leaky_bucket()
            else:
                allowed = False

            if allowed:
                self._metrics["allowed_requests"] += 1
            else:
                self._metrics["denied_requests"] += 1
                self._metrics["last_denied_time"] = datetime.now()

            return allowed

    def allow_request_sync(self, identifier: Optional[str] = None) -> bool:
        """Synchronous version of allow_request."""
        import threading

        if self._sync_lock is None:
            self._sync_lock = threading.Lock()

        with self._sync_lock:
            self._metrics["total_requests"] += 1

            if self.config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                allowed = self._check_sliding_window()
            elif self.config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                allowed = self._check_token_bucket()
            elif self.config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
                allowed = self._check_fixed_window()
            elif self.config.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
                allowed = self._check_leaky_bucket()
            else:
                allowed = False

            if allowed:
                self._metrics["allowed_requests"] += 1
            else:
                self._metrics["denied_requests"] += 1
                self._metrics["last_denied_time"] = datetime.now()

            return allowed

    def _check_sliding_window(self) -> bool:
        """Check rate limit using sliding window algorithm."""
        now = time.time()
        cutoff = now - self.config.time_window

        # Remove old requests
        while self._requests and self._requests[0] < cutoff:
            self._requests.popleft()

        # Check limit
        if len(self._requests) >= self.config.max_requests:
            return False

        # Add new request
        self._requests.append(now)
        return True

    def _check_token_bucket(self) -> bool:
        """Check rate limit using token bucket algorithm."""
        now = time.time()
        elapsed = now - self._last_update

        # Refill tokens
        refill_rate = self.config.max_requests / self.config.time_window
        self._tokens = min(
            self.config.burst_size or self.config.max_requests,
            self._tokens + (elapsed * refill_rate),
        )
        self._last_update = now

        # Check if we have tokens
        if self._tokens >= 1:
            self._tokens -= 1
            return True

        return False

    def _check_fixed_window(self) -> bool:
        """Check rate limit using fixed window algorithm."""
        now = time.time()

        # Check if we need to reset window
        if now - self._window_start >= self.config.time_window:
            self._window_start = now
            self._window_count = 0

        # Check limit
        if self._window_count >= self.config.max_requests:
            return False

        self._window_count += 1
        return True

    def _check_leaky_bucket(self) -> bool:
        """Check rate limit using leaky bucket algorithm."""
        now = time.time()
        elapsed = now - self._last_update

        # Leak the bucket
        leak_amount = elapsed * (self.config.leak_rate or 1.0)
        self._bucket_level = max(0, self._bucket_level - leak_amount)
        self._last_update = now

        # Check if bucket has room
        if self._bucket_level >= self.config.max_requests:
            return False

        self._bucket_level += 1
        return True

    async def wait_if_needed(self, identifier: Optional[str] = None) -> None:
        """Wait until request can be made without exceeding rate limit.

        Args:
            identifier: Optional identifier for per-key rate limiting
        """
        while not await self.allow_request(identifier):
            # Calculate wait time based on algorithm
            if self.config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                if self._requests:
                    oldest = self._requests[0]
                    wait_time = (oldest + self.config.time_window) - time.time()
                else:
                    wait_time = 0.1
            elif self.config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                refill_rate = self.config.max_requests / self.config.time_window
                wait_time = (1 - self._tokens) / refill_rate if refill_rate > 0 else 0.1
            else:
                wait_time = 0.1  # Default wait

            wait_time = max(0.01, min(wait_time, 1.0))  # Clamp between 10ms and 1s
            await asyncio.sleep(wait_time)

    def reset(self) -> None:
        """Reset the rate limiter state."""
        self._requests.clear()
        self._window_start = time.time()
        self._window_count = 0
        self._tokens = float(self.config.burst_size or self.config.max_requests)
        self._last_update = time.time()
        self._bucket_level = 0.0
        self._metrics["total_requests"] = 0
        self._metrics["allowed_requests"] = 0
        self._metrics["denied_requests"] = 0
        self._metrics["last_denied_time"] = None

    def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiter metrics."""
        metrics = self._metrics.copy()
        metrics["algorithm"] = self.config.algorithm.value
        metrics["max_requests"] = self.config.max_requests
        metrics["time_window"] = self.config.time_window

        # Add algorithm-specific metrics
        if self.config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            metrics["current_window_requests"] = len(self._requests)
        elif self.config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            metrics["available_tokens"] = self._tokens
        elif self.config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            metrics["current_window_count"] = self._window_count
        elif self.config.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
            metrics["bucket_level"] = self._bucket_level

        return metrics


class MultiTierRateLimiter:
    """Rate limiter with multiple tiers/levels."""

    def __init__(self):
        """Initialize multi-tier rate limiter."""
        self._tiers: Dict[str, RateLimiter] = {}
        self._lock = asyncio.Lock()

    def add_tier(
        self,
        name: str,
        max_requests: int,
        time_window: float = 60.0,
        algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW,
    ) -> None:
        """Add a rate limit tier.

        Args:
            name: Name of the tier (e.g., "per_second", "per_minute", "per_hour")
            max_requests: Maximum requests for this tier
            time_window: Time window in seconds
            algorithm: Algorithm to use for this tier
        """
        self._tiers[name] = RateLimiter(
            max_requests=max_requests, time_window=time_window, algorithm=algorithm
        )

    async def allow_request(self, identifier: Optional[str] = None) -> bool:
        """Check if request is allowed across all tiers.

        Args:
            identifier: Optional identifier for per-key rate limiting

        Returns:
            True if allowed by all tiers, False otherwise
        """
        async with self._lock:
            for tier in self._tiers.values():
                if not await tier.allow_request(identifier):
                    return False
            return True

    def reset(self, tier_name: Optional[str] = None) -> None:
        """Reset one or all tiers.

        Args:
            tier_name: Name of tier to reset, or None to reset all
        """
        if tier_name:
            if tier_name in self._tiers:
                self._tiers[tier_name].reset()
        else:
            for tier in self._tiers.values():
                tier.reset()

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all tiers."""
        return {name: tier.get_metrics() for name, tier in self._tiers.items()}


class DistributedRateLimiter:
    """Rate limiter with hooks for distributed systems."""

    def __init__(
        self,
        local_limiter: RateLimiter,
        sync_callback: Optional[Callable] = None,
        get_global_count: Optional[Callable] = None,
    ):
        """Initialize distributed rate limiter.

        Args:
            local_limiter: Local rate limiter instance
            sync_callback: Callback to sync with distributed state
            get_global_count: Callback to get global request count
        """
        self._local = local_limiter
        self._sync_callback = sync_callback
        self._get_global_count = get_global_count
        self._last_sync = time.time()
        self._sync_interval = 5.0  # Sync every 5 seconds

    async def allow_request(self, identifier: Optional[str] = None) -> bool:
        """Check if request is allowed, considering distributed state."""
        # Sync if needed
        now = time.time()
        if self._sync_callback and (now - self._last_sync) > self._sync_interval:
            await self._sync_callback()
            self._last_sync = now

        # Check global count if available
        if self._get_global_count:
            global_count = await self._get_global_count()
            if global_count >= self._local.config.max_requests:
                return False

        # Check local limiter
        return await self._local.allow_request(identifier)


# Factory functions for common rate limiting scenarios
def create_api_rate_limiter() -> RateLimiter:
    """Create rate limiter for API endpoints (100 requests per minute)."""
    return RateLimiter(
        max_requests=100, time_window=60.0, algorithm=RateLimitAlgorithm.SLIDING_WINDOW
    )


def create_database_rate_limiter() -> RateLimiter:
    """Create rate limiter for database operations (1000 per minute with bursts)."""
    return RateLimiter(
        max_requests=1000,
        time_window=60.0,
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        burst_size=50,
    )


def create_webhook_rate_limiter() -> MultiTierRateLimiter:
    """Create multi-tier rate limiter for webhooks."""
    limiter = MultiTierRateLimiter()
    limiter.add_tier("per_second", max_requests=10, time_window=1.0)
    limiter.add_tier("per_minute", max_requests=100, time_window=60.0)
    limiter.add_tier("per_hour", max_requests=1000, time_window=3600.0)
    return limiter


def create_user_rate_limiter() -> RateLimiter:
    """Create rate limiter for per-user actions (60 per minute)."""
    return RateLimiter(
        max_requests=60, time_window=60.0, algorithm=RateLimitAlgorithm.LEAKY_BUCKET
    )
