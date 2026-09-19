from __future__ import annotations

import asyncio

from clingate_lib.consumer import backoff_seconds, consume
from clingate_lib.memory import MemoryQueue
from clingate_lib.model import PoisonMessage


async def _drain(queue, handler, *, seconds=0.3, concurrency=1):
    stop = asyncio.Event()
    task = asyncio.create_task(
        consume(queue, handler, stop, concurrency=concurrency, wait_seconds=0, idle_sleep=0.01)
    )
    await asyncio.sleep(seconds)
    stop.set()
    await task


async def test_success_deletes():
    q = MemoryQueue()
    q.send("a")
    seen = []

    async def h(m):
        seen.append(m.body)

    await _drain(q, h)
    assert seen == ["a"] and q.depth() == 0 and q.inflight() == 0


async def test_transient_failure_is_redelivered_until_it_succeeds():
    q = MemoryQueue()
    q.send("a")
    attempts = []

    async def h(m):
        attempts.append(m.receive_count)
        if len(attempts) < 3:
            raise RuntimeError("boom")

    await _drain(q, h, seconds=0.6)
    assert attempts == [1, 2, 3] and q.depth() == 0 and q.inflight() == 0


async def test_poison_is_not_deleted():
    q = MemoryQueue()
    q.send("a")

    async def h(m):
        raise PoisonMessage("bad")

    await _drain(q, h)
    assert q.inflight() == 1  # left for SQS redrive -> DLQ


async def test_concurrency_is_bounded():
    q = MemoryQueue()
    for i in range(12):
        q.send(str(i))
    live = peak = 0

    async def h(m):
        nonlocal live, peak
        live += 1
        peak = max(peak, live)
        await asyncio.sleep(0.03)
        live -= 1

    await _drain(q, h, seconds=0.8, concurrency=3)
    assert peak <= 3 and q.depth() == 0


def test_backoff_is_exponential_and_capped():
    assert [backoff_seconds(n) for n in (1, 2, 3, 4)] == [2, 4, 8, 16]
    assert backoff_seconds(50) == 300
