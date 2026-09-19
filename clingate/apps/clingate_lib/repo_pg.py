"""PostgreSQL Repository. Every transaction sets app.tenant_id first; row-level security
(FORCE) then scopes each statement to that tenant."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import datetime

import psycopg
from psycopg_pool import ConnectionPool

from .ids import export_id as make_export_id
from .model import Observation
from .repo import CommitResult, Destination, ExportJob, ExportRef


class PgRepository:
    def __init__(self, dsn: str, *, min_size: int = 1, max_size: int = 8) -> None:
        self._pool = ConnectionPool(dsn, min_size=min_size, max_size=max_size, open=True)

    def close(self) -> None:
        self._pool.close()

    @contextmanager
    def _tx(self, tenant_id: str) -> Iterator[psycopg.Cursor]:
        with self._pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
            cur.execute("SELECT set_config('app.tenant_id', %s, true)", (tenant_id,))
            yield cur

    def commit_ingest(
        self,
        *,
        tenant_id: str,
        client_id: str,
        ingest_id: str,
        source: str,
        idempotency_key: str,
        raw_key: str,
        raw_sha256: str,
        received_at: datetime,
        pseudonym: str,
        device_external_id: str | None,
        observations: Sequence[Observation],
    ) -> CommitResult:
        with self._tx(tenant_id) as cur:
            cur.execute(
                """INSERT INTO ingest_events
                   (id, tenant_id, client_id, source, idempotency_key, raw_s3_key, raw_sha256,
                    received_at, status)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'accepted')
                   ON CONFLICT (tenant_id, source, idempotency_key) DO NOTHING""",
                (
                    ingest_id,
                    tenant_id,
                    client_id,
                    source,
                    idempotency_key,
                    raw_key,
                    raw_sha256,
                    received_at,
                ),
            )
            cur.execute(
                "SELECT id, status FROM ingest_events "
                "WHERE tenant_id=%s AND source=%s AND idempotency_key=%s",
                (tenant_id, source, idempotency_key),
            )
            event_id, status = cur.fetchone()
            event_id = str(event_id)
            duplicate = status == "parsed"
            if not duplicate:
                cur.execute(
                    """INSERT INTO subjects (tenant_id, pseudonym) VALUES (%s,%s)
                       ON CONFLICT (tenant_id, pseudonym) DO UPDATE SET pseudonym=EXCLUDED.pseudonym
                       RETURNING id""",
                    (tenant_id, pseudonym),
                )
                subject_id = cur.fetchone()[0]
                device_id = None
                if device_external_id:
                    cur.execute(
                        """INSERT INTO devices (tenant_id, external_id) VALUES (%s,%s)
                           ON CONFLICT (tenant_id, external_id)
                           DO UPDATE SET external_id=EXCLUDED.external_id RETURNING id""",
                        (tenant_id, device_external_id),
                    )
                    device_id = cur.fetchone()[0]
                cur.executemany(
                    """INSERT INTO observations
                       (tenant_id, subject_id, device_id, ingest_event_id, seq, code_system, code,
                        value_num, value_text, unit, observed_at, received_at)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (tenant_id, ingest_event_id, seq, observed_at) DO NOTHING""",
                    [
                        (
                            tenant_id,
                            subject_id,
                            device_id,
                            event_id,
                            o.seq,
                            o.code_system,
                            o.code,
                            o.value_num,
                            o.value_text,
                            o.unit,
                            o.observed_at,
                            received_at,
                        )
                        for o in observations
                    ],
                )
                cur.execute("UPDATE ingest_events SET status='parsed' WHERE id=%s", (event_id,))
                cur.execute("SELECT id FROM export_destinations WHERE enabled")
                for (dest_id,) in cur.fetchall():
                    cur.execute(
                        """INSERT INTO exports (id, tenant_id, ingest_event_id, destination_id)
                           VALUES (%s,%s,%s,%s) ON CONFLICT (ingest_event_id, destination_id) DO NOTHING""",
                        (make_export_id(event_id, str(dest_id)), tenant_id, event_id, dest_id),
                    )
            cur.execute(
                "SELECT id, destination_id FROM exports "
                "WHERE ingest_event_id=%s AND status='pending' AND enqueued_at IS NULL",
                (event_id,),
            )
            pending = tuple(ExportRef(str(e), str(d)) for e, d in cur.fetchall())
        return CommitResult(duplicate=duplicate, pending_exports=pending)

    def quarantine(
        self,
        *,
        tenant_id: str,
        client_id: str,
        ingest_id: str,
        source: str,
        idempotency_key: str,
        raw_key: str,
        raw_sha256: str,
        received_at: datetime,
    ) -> None:
        with self._tx(tenant_id) as cur:
            cur.execute(
                """INSERT INTO ingest_events
                   (id, tenant_id, client_id, source, idempotency_key, raw_s3_key, raw_sha256,
                    received_at, status)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'quarantined')
                   ON CONFLICT (tenant_id, source, idempotency_key)
                   DO UPDATE SET status='quarantined' WHERE ingest_events.status <> 'parsed'""",
                (
                    ingest_id,
                    tenant_id,
                    client_id,
                    source,
                    idempotency_key,
                    raw_key,
                    raw_sha256,
                    received_at,
                ),
            )

    def mark_export_enqueued(self, tenant_id: str, export_ids: Sequence[str]) -> None:
        if not export_ids:
            return
        with self._tx(tenant_id) as cur:
            cur.execute(
                "UPDATE exports SET enqueued_at=now() WHERE id = ANY(%s::uuid[])",
                (list(export_ids),),
            )

    def load_export(self, tenant_id: str, export_id: str) -> ExportJob | None:
        with self._tx(tenant_id) as cur:
            cur.execute(
                """SELECT x.ingest_event_id, x.status, d.id, d.host, d.port, d.max_connections,
                          d.sending_app, d.sending_facility, d.receiving_app, d.receiving_facility,
                          d.tls_ca_ref
                   FROM exports x JOIN export_destinations d ON d.id = x.destination_id
                   WHERE x.id=%s""",
                (export_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            event_id, status, *dest = row
            destination = Destination(str(dest[0]), *dest[1:])
            cur.execute(
                """SELECT s.pseudonym, o.seq, o.code_system, o.code, o.value_num, o.value_text,
                          o.unit, o.observed_at
                   FROM observations o JOIN subjects s ON s.id = o.subject_id
                   WHERE o.ingest_event_id=%s ORDER BY o.seq""",
                (event_id,),
            )
            rows = cur.fetchall()
        if not rows:
            return None
        obs = tuple(
            Observation(seq=r[1], code_system=r[2], code=r[3], value_num=r[4], value_text=r[5],
                        unit=r[6], observed_at=r[7])
            for r in rows
        )  # fmt: skip
        return ExportJob(export_id, tenant_id, str(event_id), status, destination, rows[0][0], obs)

    def record_export_attempt(
        self, tenant_id: str, export_id: str, *, ack_code: str | None, status: str
    ) -> None:
        with self._tx(tenant_id) as cur:
            cur.execute(
                """UPDATE exports SET attempts = attempts + 1, last_ack_code = %s, status = %s,
                          acked_at = CASE WHEN %s = 'acked' THEN now() ELSE acked_at END
                   WHERE id=%s""",
                (ack_code, status, status, export_id),
            )

    def count_events(self, tenant_id: str, source: str, idempotency_keys: Sequence[str]) -> int:
        with self._tx(tenant_id) as cur:
            cur.execute(
                "SELECT count(*) FROM ingest_events WHERE source=%s AND idempotency_key = ANY(%s)",
                (source, list(idempotency_keys)),
            )
            return cur.fetchone()[0]

    def count_observations(self, tenant_id: str) -> int:
        with self._tx(tenant_id) as cur:
            cur.execute("SELECT count(*) FROM observations")
            return cur.fetchone()[0]

    def unfinished_exports(self, tenant_id: str) -> int:
        with self._tx(tenant_id) as cur:
            cur.execute("SELECT count(*) FROM exports WHERE status='pending'")
            return cur.fetchone()[0]
