from __future__ import annotations

import hashlib
from datetime import UTC, datetime

import pytest

from clingate_lib.ids import ingest_id, raw_key
from clingate_lib.memory import MemoryQueue
from clingate_lib.model import ExportPointer, PointerMessage, PoisonMessage
from clingate_lib.repo_memory import MemoryRepository
from clingate_sim.generate import device_batch, hl7_message
from clingate_worker.core import process_ingest
from tests.conftest import TENANT_A, TENANT_B, make_destination


def _pointer(store, source: str, key: str, data: bytes, tenant=TENANT_A) -> str:
    k = raw_key(tenant, source, key)
    store.put_if_absent(k, data, hashlib.sha256(data).hexdigest())
    return PointerMessage(
        ingest_id=ingest_id(tenant, source, key), tenant_id=tenant, client_id="c", source=source,
        idempotency_key=key, s3_key=k, sha256=hashlib.sha256(data).hexdigest(),
        received_at=datetime.now(UTC).isoformat(), trace_id="t",
    ).to_json()  # fmt: skip


@pytest.fixture
def repo():
    return MemoryRepository({TENANT_A: [make_destination()]})


@pytest.fixture
def export_q():
    return MemoryQueue()


def test_http_batch_is_normalised_and_export_enqueued(store, repo, export_q):
    key, raw = device_batch(1, 1, n_obs=5)
    assert (
        process_ingest(
            _pointer(store, "http", key, raw), store=store, repo=repo, export_queue=export_q
        )
        == "processed"
    )
    assert repo.count_observations(TENANT_A) == 5
    assert (
        len(export_q.sent) == 1 and ExportPointer.from_json(export_q.sent[0]).tenant_id == TENANT_A
    )


def test_hl7_message_is_normalised(store, repo, export_q):
    key, text = hl7_message(1, 1, n_obs=7, with_identifiers=False)
    process_ingest(
        _pointer(store, "mllp", key, text.encode()), store=store, repo=repo, export_queue=export_q
    )
    assert repo.count_observations(TENANT_A) == 7


def test_H2_redelivery_does_not_duplicate_observations_or_exports(store, repo, export_q):
    key, raw = device_batch(1, 2, n_obs=4)
    body = _pointer(store, "http", key, raw)
    for _ in range(3):
        process_ingest(body, store=store, repo=repo, export_queue=export_q)
    assert repo.count_observations(TENANT_A) == 4
    assert len(export_q.sent) == 1


def test_crash_between_commit_and_enqueue_is_repaired_on_redelivery(store, repo, export_q):
    key, raw = device_batch(1, 3)
    body = _pointer(store, "http", key, raw)
    export_q.fail_on_send = True
    with pytest.raises(OSError):
        process_ingest(body, store=store, repo=repo, export_queue=export_q)
    assert repo.count_observations(TENANT_A) == 30 and not export_q.sent  # committed, not enqueued
    export_q.fail_on_send = False
    assert process_ingest(body, store=store, repo=repo, export_queue=export_q) == "duplicate"
    assert len(export_q.sent) == 1  # the missing export was re-driven
    process_ingest(body, store=store, repo=repo, export_queue=export_q)
    assert len(export_q.sent) == 1  # and only once


def test_H4_checksum_mismatch_is_quarantined(store, repo, export_q):
    key, raw = device_batch(1, 4)
    body = _pointer(store, "http", key, raw)
    store.objects[raw_key(TENANT_A, "http", key)] = raw + b" "  # corrupted after the fact
    with pytest.raises(PoisonMessage):
        process_ingest(body, store=store, repo=repo, export_queue=export_q)
    assert repo.count_observations(TENANT_A) == 0
    assert repo.count_events(TENANT_A, "http", [key]) == 1  # recorded as quarantined, raw kept


def test_unparseable_payload_is_quarantined_not_dropped(store, repo, export_q):
    body = _pointer(store, "http", "bad-batch-0001", b'{"not": "a batch"}')
    with pytest.raises(PoisonMessage):
        process_ingest(body, store=store, repo=repo, export_queue=export_q)
    assert repo.count_events(TENANT_A, "http", ["bad-batch-0001"]) == 1
    assert "raw/" in next(iter(store.objects))  # the raw copy is still there


def test_H3_tenant_without_destination_gets_no_exports(store, export_q):
    repo = MemoryRepository({TENANT_A: [make_destination()]})
    key, raw = device_batch(1, 5)
    process_ingest(
        _pointer(store, "http", key, raw, tenant=TENANT_B),
        store=store,
        repo=repo,
        export_queue=export_q,
    )
    assert repo.count_observations(TENANT_B) == 30 and repo.count_observations(TENANT_A) == 0
    assert not export_q.sent
