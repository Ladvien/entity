import asyncio

import pytest
from pipeline.exceptions import CircuitBreakerTripped
from pipeline.reliability import CircuitBreaker, RetryPolicy


@pytest.mark.integration
async def test_retry_policy_recovers():
    attempts = 0

    async def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("boom")
        return "ok"

    policy = RetryPolicy(attempts=5, backoff=0)
    result = await policy.execute(flaky)
    assert result == "ok"
    assert attempts == 3


@pytest.mark.integration
async def test_circuit_breaker_trips():
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    async def fail() -> None:
        raise RuntimeError("bad")

    with pytest.raises(RuntimeError):
        await breaker.call(fail)
    with pytest.raises(RuntimeError):
        await breaker.call(fail)

    with pytest.raises(CircuitBreakerTripped):
        await breaker.call(fail)

    await asyncio.sleep(0.11)

    with pytest.raises(RuntimeError):
        await breaker.call(fail)
