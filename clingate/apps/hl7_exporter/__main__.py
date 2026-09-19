from __future__ import annotations

import asyncio
import os

from clingate_lib.config import Settings
from clingate_lib.consumer import consume
from clingate_lib.logging import configure
from clingate_lib.ports import QueueMessage
from clingate_lib.wiring import build_queue, build_repo

from .core import process_export
from .pool import DestinationPool


async def main() -> None:
    configure("hl7_exporter")
    s = Settings.from_env()
    repo, queue, pool = build_repo(s), build_queue(s, s.export_queue_url), DestinationPool()

    async def handler(msg: QueueMessage) -> None:
        await process_export(msg.body, repo=repo, pool=pool, processing_id=s.processing_id)

    # concurrency <= destination.max_connections x replicas: never exceed the far end's budget
    await consume(
        queue,
        handler,
        asyncio.Event(),
        concurrency=int(os.environ.get("CLINGATE_CONCURRENCY", "2")),
    )


if __name__ == "__main__":
    asyncio.run(main())
