from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from clingate_lib.ids import ingest_id, raw_key
from clingate_lib.memory import MemoryQueue
from clingate_lib.model import PointerMessage
from clingate_lib.repo_memory import MemoryRepository
from clingate_ops.reconcile import reconcile
from clingate_sim.generate import device_batch
from clingate_worker.core import process_ingest
from tests.conftest import TENANT_A, make_destination


def _ingest(store, repo, n):
    key, raw = device_batch(1, n, n_obs=2)
    k = raw_key(TENANT_A, "http", key)
    sha = hashlib.sha256(raw).hexdigest()
    store.put_if_absent(k, raw, sha)
    body = PointerMessage(ingest_id(TENANT_A, "http", key), TENANT_A, "c", "http", key, k, sha,
                          datetime.now(UTC).isoformat(), "t").to_json()  # fmt: skip
    process_ingest(body, store=store, repo=repo, export_queue=MemoryQueue())
    return key


def test_clean_run_passes(store):
    repo = MemoryRepository()
    keys = [_ingest(store, repo, n) for n in range(5)]
    ledger = [{"idempotency_key": k, "status": 202} for k in keys + keys[:1]]  # one duplicate sent
    rep = reconcile(
        ledger, tenant_id=TENANT_A, source="http", store=store, repo=repo, expected_observations=10
    )
    assert rep.ok, rep.details


def test_lost_object_is_detected(store):
    repo = MemoryRepository()
    keys = [_ingest(store, repo, n) for n in range(3)]
    del store.objects[raw_key(TENANT_A, "http", keys[0])]
    rep = reconcile([{"idempotency_key": k, "status": 202} for k in keys],
                    tenant_id=TENANT_A, source="http", store=store, repo=repo)  # fmt: skip
    assert not rep.ok and not rep.checks["I1 acked => raw object exists"]


def test_acked_but_never_processed_is_detected(store):
    repo = MemoryRepository()
    _ingest(store, repo, 0)
    ghost_key, raw = device_batch(1, 99)
    store.put_if_absent(
        raw_key(TENANT_A, "http", ghost_key), raw, "0" * 64
    )  # stored, never processed
    rep = reconcile([{"idempotency_key": ghost_key, "status": 202}],
                    tenant_id=TENANT_A, source="http", store=store, repo=repo)  # fmt: skip
    assert not rep.checks["I2 one ingest_event per unique key"]


def test_pending_export_is_detected(store):
    repo = MemoryRepository({TENANT_A: [make_destination()]})
    key = _ingest(store, repo, 0)
    rep = reconcile(
        [{"idempotency_key": key, "status": 202}],
        tenant_id=TENANT_A,
        source="http",
        store=store,
        repo=repo,
    )
    assert not rep.checks["I4 no export left pending"]


def test_non_acked_ledger_rows_are_ignored(store):
    rep = reconcile([{"idempotency_key": "never-stored", "status": 503}],
                    tenant_id=TENANT_A, source="http", store=MemoryRepository and store, repo=MemoryRepository())  # fmt: skip
    assert rep.ok
