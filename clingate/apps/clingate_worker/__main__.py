from __future__ import annotations

import asyncio
import functools
import os

from clingate_lib.config import Settings
from clingate_lib.consumer import consume
from clingate_lib.logging import configure
from clingate_lib.ports import QueueMessage
from clingate_lib.wiring import build_queue, build_repo, build_store

from .core import process_ingest


async def main() -> None:
    configure("worker")
    s = Settings.from_env()
    store, repo = build_store(s), build_repo(s)
    ingest_q, export_q = build_queue(s, s.ingest_queue_url), build_queue(s, s.export_queue_url)
    handle = functools.partial(process_ingest, store=store, repo=repo, export_queue=export_q)

    async def handler(msg: QueueMessage) -> None:
        await asyncio.to_thread(handle, msg.body)

    # concurrency is bounded by the DB connection budget: pods x pool <= budget
    await consume(
        ingest_q,
        handler,
        asyncio.Event(),
        concurrency=int(os.environ.get("CLINGATE_CONCURRENCY", "4")),
    )


if __name__ == "__main__":
    asyncio.run(main())
