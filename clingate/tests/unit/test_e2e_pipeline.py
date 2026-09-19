"""Whole pipeline in one process, over real sockets, with in-memory S3/SQS/DB:
sender-sim -> MLLP listener -> ingest-q -> worker -> export-q -> exporter -> sink-sim,
then the same reconciliation the load tests use."""

from __future__ import annotations

import asyncio
import functools

from clingate_lib.consumer import consume
from clingate_lib.memory import MemoryQueue
from clingate_lib.mllp import serve
from clingate_lib.repo_memory import MemoryRepository
from clingate_ops.reconcile import load_ledger, reconcile
from clingate_sim.sender import dump
from clingate_sim.sink import Sink
from clingate_worker.core import process_ingest
from hl7_exporter.core import process_export
from hl7_exporter.pool import DestinationPool
from mllp_listener.app import Listener
from tests.conftest import TENANT_A, make_destination

COUNT, N_OBS = 60, 12


async def test_pipeline_end_to_end_with_reconciliation(registry, store, queue, audit, tmp_path):
    sink = Sink(latency_ms=2)
    sink_server = await serve(sink.handle, "127.0.0.1", 0)
    repo = MemoryRepository({TENANT_A: [make_destination(sink_server.sockets[0].getsockname()[1])]})
    listener = Listener(registry=registry, store=store, queue=queue, audit=audit,
                        processing_id="T", dev_client_id="lab-a")  # fmt: skip
    lserver = await serve(listener.handle, "127.0.0.1", 0)
    ledger = str(tmp_path / "ledger.jsonl")

    async with lserver, sink_server:
        summary = await dump(
            "127.0.0.1", lserver.sockets[0].getsockname()[1],
            count=COUNT, connections=4, seed=7, ledger_path=ledger, duplicate_rate=0.1,
        )  # fmt: skip
        assert summary["non_aa"] == 0 and summary["sent"] > COUNT  # duplicates were sent

        export_q = MemoryQueue()
        while msgs := queue.receive(10, 0):
            for m in msgs:
                process_ingest(m.body, store=store, repo=repo, export_queue=export_q)
                queue.delete(m)

        pool = DestinationPool(timeout=2.0)
        handler = functools.partial(process_export, repo=repo, pool=pool, processing_id="T")

        async def on_msg(m):
            await handler(m.body)

        stop = asyncio.Event()
        task = asyncio.create_task(
            consume(export_q, on_msg, stop, concurrency=2, wait_seconds=0, idle_sleep=0.01)
        )
        for _ in range(300):
            if repo.unfinished_exports(TENANT_A) == 0 and export_q.depth() == 0:
                break
            await asyncio.sleep(0.02)
        stop.set()
        await task
        await pool.close()  # the sink server waits for open connections on exit

    report = reconcile(load_ledger(ledger), tenant_id=TENANT_A, source="mllp", store=store, repo=repo,
                       expected_observations=COUNT * N_OBS)  # fmt: skip
    assert report.ok, report.details
    assert len(set(sink.control_ids)) == COUNT  # duplicates never produced extra exports
    assert not any("SINTETICO" in t for t in sink.received)  # identifiers never reached the far end
