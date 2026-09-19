"""Needs Postgres. `make test-integration` starts one via docker compose and sets
CLINGATE_TEST_DSN (migrator) and CLINGATE_TEST_APP_DSN (app_rw)."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal

import psycopg
import pytest

from clingate_lib.ids import ingest_id, raw_key
from clingate_lib.model import Observation
from clingate_lib.repo_pg import PgRepository
from clingate_ops.migrate import migrate
from tests.conftest import TENANT_A, TENANT_B

MIG = os.environ.get("CLINGATE_TEST_DSN")
APP = os.environ.get("CLINGATE_TEST_APP_DSN")
DEST_A = "33333333-3333-3333-3333-333333333333"
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not (MIG and APP), reason="CLINGATE_TEST_DSN / CLINGATE_TEST_APP_DSN not set"
    ),
]
NOW = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def db():
    with psycopg.connect(MIG, autocommit=True) as c:  # start from a clean schema
        c.execute(
            "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT USAGE ON SCHEMA public TO app_rw, auditor_ro"
        )
    migrate(MIG)
    with psycopg.connect(MIG, autocommit=True) as c:
        for t in (TENANT_A, TENANT_B):
            c.execute("INSERT INTO tenants (id, name) VALUES (%s, %s)", (t, f"tenant-{t[:2]}"))
        c.execute(
            "SELECT set_config('app.tenant_id', %s, false)", (TENANT_A,)
        )  # FORCE RLS binds the owner too
        c.execute(
            "INSERT INTO export_destinations (id, tenant_id, name, host, port, receiving_app, receiving_facility)"
            " VALUES (%s, %s, 'sponsor', '127.0.0.1', 2576, 'SPONSOR', 'HQ')", (DEST_A, TENANT_A)
        )  # fmt: skip
    repo = PgRepository(APP)
    yield repo
    repo.close()


def _kw(tenant, key, n_obs=3, at=NOW):
    return dict(
        tenant_id=tenant, client_id="c", ingest_id=ingest_id(tenant, "http", key), source="http",
        idempotency_key=key, raw_key=raw_key(tenant, "http", key), raw_sha256="0" * 64, received_at=NOW,
        pseudonym="subj-1", device_external_id="dev-1",
        observations=[Observation(i, "LOINC", "8867-4", at, Decimal(60 + i), None, "/min") for i in range(1, n_obs + 1)],
    )  # fmt: skip


def test_commit_is_idempotent_and_exports_are_redriven(db):
    r1 = db.commit_ingest(**_kw(TENANT_A, "k-idem"))
    assert not r1.duplicate and len(r1.pending_exports) == 1
    r2 = db.commit_ingest(**_kw(TENANT_A, "k-idem"))  # redelivery before enqueue was recorded
    assert r2.duplicate and r2.pending_exports == r1.pending_exports
    assert db.count_observations(TENANT_A) == 3  # no duplicate rows
    db.mark_export_enqueued(TENANT_A, [e.export_id for e in r1.pending_exports])
    assert db.commit_ingest(**_kw(TENANT_A, "k-idem")).pending_exports == ()


def test_H3_row_level_security_isolates_tenants(db):
    db.commit_ingest(**_kw(TENANT_B, "k-b"))
    assert db.count_observations(TENANT_B) == 3
    assert db.count_events(TENANT_A, "http", ["k-b"]) == 0  # A cannot see B's event
    assert db.count_events(TENANT_B, "http", ["k-b"]) == 1
    with psycopg.connect(APP) as c:  # app role with NO tenant set sees nothing at all
        assert c.execute("SELECT count(*) FROM observations").fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM ingest_events").fetchone()[0] == 0


def test_H3_cannot_write_a_row_for_another_tenant(db):
    with psycopg.connect(APP) as c, pytest.raises(psycopg.errors.InsufficientPrivilege):
        c.execute("SELECT set_config('app.tenant_id', %s, true)", (TENANT_A,))
        c.execute("INSERT INTO subjects (tenant_id, pseudonym) VALUES (%s, 'x')", (TENANT_B,))


def test_app_role_cannot_bypass_rls_or_alter_schema(db):
    with psycopg.connect(APP) as c, pytest.raises(psycopg.errors.InsufficientPrivilege):
        c.execute("ALTER TABLE observations DISABLE ROW LEVEL SECURITY")
    with psycopg.connect(APP) as c, pytest.raises(psycopg.errors.InsufficientPrivilege):
        c.execute("DELETE FROM audit_events")  # audit is INSERT-only


def test_quarantine_never_overwrites_a_parsed_event(db):
    db.commit_ingest(**_kw(TENANT_A, "k-q1"))
    kw = _kw(TENANT_A, "k-q1")
    db.quarantine(**{k: kw[k] for k in ("tenant_id", "client_id", "ingest_id", "source", "idempotency_key",
                                        "raw_key", "raw_sha256", "received_at")})  # fmt: skip
    assert db.commit_ingest(**kw).duplicate  # still 'parsed'


def test_load_export_roundtrip_and_ack_flow(db):
    r = db.commit_ingest(**_kw(TENANT_A, "k-exp", n_obs=2))
    eid = r.pending_exports[0].export_id
    job = db.load_export(TENANT_A, eid)
    assert job.pseudonym == "subj-1" and len(job.observations) == 2 and job.destination.port == 2576
    assert db.load_export(TENANT_B, eid) is None  # RLS: other tenant cannot load it
    db.record_export_attempt(TENANT_A, eid, ack_code="AA", status="acked")
    assert db.load_export(TENANT_A, eid).status == "acked"


def test_observations_land_in_monthly_partition(db):
    db.commit_ingest(**_kw(TENANT_A, "k-part", at=datetime(2026, 11, 15, tzinfo=UTC)))
    with psycopg.connect(MIG) as c:
        n = c.execute("SELECT count(*) FROM observations_2026_11").fetchone()[0]
    assert n >= 3
