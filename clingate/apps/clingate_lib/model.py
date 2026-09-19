from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Observation:
    seq: int
    code_system: str
    code: str
    observed_at: datetime
    value_num: Decimal | None = None
    value_text: str | None = None
    unit: str | None = None
    code_text: str | None = None
    status: str | None = None
    abnormal: str | None = None


@dataclass(frozen=True)
class ParsedPayload:
    pseudonym: str
    device_external_id: str | None
    observations: tuple[Observation, ...]


@dataclass(frozen=True)
class Client:
    client_id: str
    tenant_id: str
    kind: str
    enabled: bool = True
    cert_sha256: str | None = None
    sending_application: str | None = None
    sending_facility: str | None = None


@dataclass(frozen=True)
class PointerMessage:
    """What travels through ingest-q. Pointers only: no payload, no PHI."""

    ingest_id: str
    tenant_id: str
    client_id: str
    source: str
    idempotency_key: str
    s3_key: str
    sha256: str
    received_at: str
    trace_id: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

    @classmethod
    def from_json(cls, body: str) -> PointerMessage:
        return cls(**json.loads(body))


@dataclass(frozen=True)
class ExportPointer:
    export_id: str
    tenant_id: str
    trace_id: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

    @classmethod
    def from_json(cls, body: str) -> ExportPointer:
        return cls(**json.loads(body))


class PoisonMessage(Exception):  # noqa: N818 - domain term
    """Deterministic failure: retrying cannot help. Falls through to the DLQ."""


class RetryableError(Exception):
    """Transient failure: leave the message for redelivery."""
