from __future__ import annotations

import hashlib
import uuid

_NS = uuid.UUID("6f0c2c1e-7a4b-4f7e-9d1a-2b3c4d5e6f70")


def ingest_id(tenant_id: str, source: str, idempotency_key: str) -> str:
    """Deterministic: API/listener, worker and reconciliation all derive the same id."""
    return str(uuid.uuid5(_NS, f"ingest|{tenant_id}|{source}|{idempotency_key}"))


def export_id(ingest_event_id: str, destination_id: str) -> str:
    return str(uuid.uuid5(_NS, f"export|{ingest_event_id}|{destination_id}"))


def raw_key(tenant_id: str, source: str, idempotency_key: str) -> str:
    """Deterministic on the idempotency key so retries address the same immutable object.
    The 2-hex prefix spreads request load across S3 prefixes."""
    digest = hashlib.sha256(f"{source}|{idempotency_key}".encode()).hexdigest()
    return f"raw/{tenant_id}/{digest[:2]}/source={source}/{digest}"


def outbound_control_id(ingest_event_id: str, destination_id: str) -> str:
    """MSH-10 for exports: identical on every retry, so a retry is a duplicate by construction."""
    return hashlib.sha256(f"{ingest_event_id}|{destination_id}".encode()).hexdigest()[:24]
