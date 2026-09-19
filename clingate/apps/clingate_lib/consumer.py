"""Queue consumption loop shared by worker and exporter.

Success -> delete. PoisonMessage -> leave it: SQS redrive moves it to the DLQ after
maxReceiveCount. Anything else -> transient: shorten/extend visibility with exponential
backoff so a struggling dependency is not hammered.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from .model import PoisonMessage
from .ports import QueueMessage, WorkQueue

log = logging.getLogger("clingate.consumer")


def backoff_seconds(receive_count: int, base: float = 2.0, cap: float = 300.0) -> int:
    return int(min(cap, base ** max(receive_count, 1)))


async def consume(
    queue: WorkQueue,
    handler: Callable[[QueueMessage], Awaitable[None]],
    stop: asyncio.Event,
    *,
    concurrency: int = 1,
    wait_seconds: int = 20,
    idle_sleep: float = 0.05,
) -> None:
    sem = asyncio.Semaphore(concurrency)

    async def run_one(msg: QueueMessage) -> None:
        try:
            await handler(msg)
            await asyncio.to_thread(queue.delete, msg)
        except PoisonMessage:
            log.warning("poison", extra={"ctx": {"reason": "poison", "attempt": msg.receive_count}})
        except Exception:
            log.warning("transient", exc_info=True, extra={"ctx": {"attempt": msg.receive_count}})
            await asyncio.to_thread(
                queue.change_visibility, msg, backoff_seconds(msg.receive_count)
            )
        finally:
            sem.release()

    tasks: set[asyncio.Task[None]] = set()
    while not stop.is_set():
        await sem.acquire()
        sem.release()
        msgs = await asyncio.to_thread(queue.receive, min(10, concurrency), wait_seconds)
        if not msgs:
            await asyncio.sleep(idle_sleep)
            continue
        for m in msgs:
            await sem.acquire()
            t = asyncio.create_task(run_one(m))
            tasks.add(t)
            t.add_done_callback(tasks.discard)
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
