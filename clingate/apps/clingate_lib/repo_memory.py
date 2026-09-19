"""In-memory Repository with the same idempotency semantics as the Postgres one."""

from __future__ import annotations

import threading
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime

from .ids import export_id as make_export_id
from .model import Observation
from .repo import CommitResult, Destination, ExportJob, ExportRef


@dataclass
class _Event:
    id: str
    tenant_id: str
    source: str
    idempotency_key: str
    status: str
    pseudonym: str = ""
    observations: list[Observation] = field(default_factory=list)


@dataclass
class _Export:
    id: str
    tenant_id: str
    ingest_event_id: str
    destination_id: str
    status: str = "pending"
    attempts: int = 0
    last_ack_code: str | None = None
    enqueued: bool = False


class MemoryRepository:
    def __init__(self, destinations: dict[str, list[Destination]] | None = None) -> None:
        self._destinations = destinations or {}
        self._events: dict[tuple[str, str, str], _Event] = {}
        self._exports: dict[str, _Export] = {}
        self._lock = threading.Lock()

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
        with self._lock:
            k = (tenant_id, source, idempotency_key)
            ev = self._events.get(k)
            duplicate = ev is not None and ev.status == "parsed"
            if ev is None:
                ev = self._events[k] = _Event(
                    ingest_id, tenant_id, source, idempotency_key, "accepted"
                )
            if not duplicate:
                ev.pseudonym = pseudonym
                ev.observations = list(observations)
                ev.status = "parsed"
                for d in self._destinations.get(tenant_id, []):
                    eid = make_export_id(ev.id, d.id)
                    self._exports.setdefault(eid, _Export(eid, tenant_id, ev.id, d.id))
            pending = tuple(
                ExportRef(x.id, x.destination_id)
                for x in self._exports.values()
                if x.ingest_event_id == ev.id and x.status == "pending" and not x.enqueued
            )
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
        with self._lock:
            k = (tenant_id, source, idempotency_key)
            ev = self._events.setdefault(
                k, _Event(ingest_id, tenant_id, source, idempotency_key, "quarantined")
            )
            if ev.status != "parsed":
                ev.status = "quarantined"

    def mark_export_enqueued(self, tenant_id: str, export_ids: Sequence[str]) -> None:
        with self._lock:
            for eid in export_ids:
                self._exports[eid].enqueued = True

    def load_export(self, tenant_id: str, export_id: str) -> ExportJob | None:
        with self._lock:
            x = self._exports.get(export_id)
            if x is None or x.tenant_id != tenant_id:
                return None
            ev = next(e for e in self._events.values() if e.id == x.ingest_event_id)
            dest = next(d for d in self._destinations[tenant_id] if d.id == x.destination_id)
            return ExportJob(
                x.id, tenant_id, ev.id, x.status, dest, ev.pseudonym, tuple(ev.observations)
            )

    def record_export_attempt(
        self, tenant_id: str, export_id: str, *, ack_code: str | None, status: str
    ) -> None:
        with self._lock:
            x = self._exports[export_id]
            x.attempts += 1
            x.last_ack_code = ack_code
            x.status = status

    def count_events(self, tenant_id: str, source: str, idempotency_keys: Sequence[str]) -> int:
        with self._lock:
            keys = set(idempotency_keys)
            return sum(
                1 for (t, s, k) in self._events if t == tenant_id and s == source and k in keys
            )

    def count_observations(self, tenant_id: str) -> int:
        with self._lock:
            return sum(
                len(e.observations) for e in self._events.values() if e.tenant_id == tenant_id
            )

    def unfinished_exports(self, tenant_id: str) -> int:
        with self._lock:
            return sum(
                1
                for x in self._exports.values()
                if x.tenant_id == tenant_id and x.status == "pending"
            )

    def export_attempts(self, export_id: str) -> int:
        return self._exports[export_id].attempts
