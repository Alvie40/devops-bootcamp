from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, datetime

import pytest

from clingate_lib import hl7
from clingate_lib.ids import export_id, ingest_id, outbound_control_id, raw_key
from clingate_lib.memory import MemoryQueue
from clingate_lib.mllp import serve
from clingate_lib.model import ExportPointer, PointerMessage, PoisonMessage, RetryableError
from clingate_lib.repo_memory import MemoryRepository
from clingate_sim.generate import device_batch, hl7_message
from clingate_sim.sink import Sink
from clingate_worker.core import process_ingest
from hl7_exporter.core import process_export
from hl7_exporter.pool import CircuitBreaker, DestinationPool
from tests.conftest import TENANT_A, make_destination


async def _setup(store, sink: Sink | None, port_override: int | None = None):
    server = port = None
    if sink is not None:
        server = await serve(sink.handle, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
    dest = make_destination(port_override if port_override is not None else port)
    repo = MemoryRepository({TENANT_A: [dest]})
    key, raw = device_batch(1, 1, n_obs=3)
    k = raw_key(TENANT_A, "http", key)
    sha = hashlib.sha256(raw).hexdigest()
    store.put_if_absent(k, raw, sha)
    export_q = MemoryQueue()
    process_ingest(
        PointerMessage(ingest_id(TENANT_A, "http", key), TENANT_A, "c", "http", key, k, sha,
                       datetime.now(UTC).isoformat(), "t").to_json(),
        store=store, repo=repo, export_queue=export_q,
    )  # fmt: skip
    return server, repo, export_q.sent[0], dest


async def _run(body, repo):
    pool = DestinationPool(timeout=1.0)
    try:
        return await process_export(body, repo=repo, pool=pool, processing_id="T")
    finally:
        await pool.close()


async def test_aa_marks_export_acked(store):
    sink = Sink()
    server, repo, body, dest = await _setup(store, sink)
    async with server:
        assert await _run(body, repo) == "acked"
    assert repo.unfinished_exports(TENANT_A) == 0
    parsed = hl7.parse_oru(sink.received[0])
    assert len(parsed.observations) == 3 and parsed.msh.receiving_app == "SPONSOR"


async def test_H2_outbound_msh10_is_identical_on_retry(store):
    sink = Sink(ae_rate=1.0)
    server, repo, body, dest = await _setup(store, sink)
    async with server:
        for _ in range(2):
            with pytest.raises(RetryableError):
                await _run(body, repo)
    eid = ExportPointer.from_json(body).export_id
    job = repo.load_export(TENANT_A, eid)
    assert sink.control_ids == [outbound_control_id(job.ingest_event_id, dest.id)] * 2


async def test_ae_is_retryable_and_stays_pending(store):
    server, repo, body, _ = await _setup(store, Sink(ae_rate=1.0))
    async with server:
        with pytest.raises(RetryableError):
            await _run(body, repo)
    assert repo.unfinished_exports(TENANT_A) == 1


async def test_ar_is_poison_and_failed(store):
    server, repo, body, _ = await _setup(store, Sink(ar_rate=1.0))
    async with server:
        with pytest.raises(PoisonMessage):
            await _run(body, repo)
    assert repo.unfinished_exports(TENANT_A) == 0  # failed, no longer pending


async def test_H5_destination_down_is_retryable(store):
    _, repo, body, _ = await _setup(store, None, port_override=1)
    with pytest.raises(RetryableError):
        await _run(body, repo)
    assert repo.unfinished_exports(TENANT_A) == 1


async def test_already_acked_is_a_noop(store):
    sink = Sink()
    server, repo, body, _ = await _setup(store, sink)
    async with server:
        await _run(body, repo)
        assert await _run(body, repo) == "already-acked"
    assert len(sink.received) == 1


async def test_pool_never_exceeds_destination_connection_budget(store):
    """max_connections=2: ten concurrent sends must never hold more than 2 connections."""
    live = peak = 0

    async def slow(frame: bytes, peer):
        nonlocal live, peak
        live += 1
        peak = max(peak, live)
        await asyncio.sleep(0.05)
        live -= 1
        return hl7.build_ack(hl7.parse_msh_lenient(frame.decode()), "AA", control_id="A").encode()

    server = await serve(slow, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    dest = make_destination(port)
    pool = DestinationPool(timeout=2.0)
    _, msg = hl7_message(1, 1)
    async with server:
        await asyncio.gather(*(pool.send(dest, msg.encode()) for _ in range(10)))
        await pool.close()  # before the server exits: it waits for open connections
    assert peak <= 2


def test_circuit_breaker_opens_and_half_opens():
    t = [0.0]
    cb = CircuitBreaker(threshold=3, reset_after=10, clock=lambda: t[0])
    for _ in range(3):
        assert cb.allow()
        cb.failure()
    assert not cb.allow()
    t[0] = 11
    assert cb.allow()  # half-open probe
    cb.success()
    assert cb.allow()


def test_export_id_is_deterministic():
    assert export_id("e", "d") == export_id("e", "d") != export_id("e", "d2")
