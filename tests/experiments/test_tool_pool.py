import asyncio

import pytest

from experiments.tool_pool.pool import ToolPool


async def _echo(value: int, delay: float = 0.01) -> int:
    await asyncio.sleep(delay)
    return value


@pytest.mark.asyncio
async def test_tool_pool_runs_tasks():
    pool = ToolPool(concurrency=2)
    await pool.start()

    futures = [await pool.submit(lambda v=v: _echo(v)) for v in range(5)]
    results = [await f for f in futures]

    await pool.stop()

    assert results == list(range(5))
    assert pool.metrics.tasks_executed == 5
    assert pool.metrics.throughput > 0
    assert pool.metrics.average_latency > 0
