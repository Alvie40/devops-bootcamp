from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from .model import Observation


@dataclass(frozen=True)
class Destination:
    id: str
    host: str
    port: int
    max_connections: int
    sending_app: str
    sending_facility: str
    receiving_app: str
    receiving_facility: str
    tls_ca_ref: str | None = None


@dataclass(frozen=True)
class ExportRef:
    export_id: str
    destination_id: str


@dataclass(frozen=True)
class CommitResult:
    duplicate: bool
    pending_exports: tuple[ExportRef, ...]


@dataclass(frozen=True)
class ExportJob:
    export_id: str
    tenant_id: str
    ingest_event_id: str
    status: str
    destination: Destination
    pseudonym: str
    observations: tuple[Observation, ...]


class Repository(Protocol):
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
        """One transaction. Idempotent: replaying it changes nothing and still returns
        any export that was recorded but never enqueued."""
        ...

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
    ) -> None: ...

    def mark_export_enqueued(self, tenant_id: str, export_ids: Sequence[str]) -> None: ...

    def load_export(self, tenant_id: str, export_id: str) -> ExportJob | None: ...

    def record_export_attempt(
        self, tenant_id: str, export_id: str, *, ack_code: str | None, status: str
    ) -> None:
        """status: 'acked' | 'failed' | 'pending' (attempt recorded, retry expected)."""
        ...

    def count_events(self, tenant_id: str, source: str, idempotency_keys: Sequence[str]) -> int: ...

    def count_observations(self, tenant_id: str) -> int: ...

    def unfinished_exports(self, tenant_id: str) -> int: ...
