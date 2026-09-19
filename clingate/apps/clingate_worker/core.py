from __future__ import annotations

import hashlib
import logging
from datetime import datetime

from pydantic import ValidationError

from clingate_lib import hl7
from clingate_lib.model import ExportPointer, ParsedPayload, PointerMessage, PoisonMessage
from clingate_lib.ports import RawStore, WorkQueue
from clingate_lib.repo import Repository
from clingate_lib.schemas import parse_batch

log = logging.getLogger("worker")


def parse_payload(source: str, raw: bytes) -> ParsedPayload:
    if source == "http":
        return parse_batch(raw)
    if source == "mllp":
        oru = hl7.parse_oru(raw.decode("utf-8"))
        return ParsedPayload(oru.pseudonym, None, oru.observations)
    raise ValueError("unknown source")


def process_ingest(body: str, *, store: RawStore, repo: Repository, export_queue: WorkQueue) -> str:
    """Every step is idempotent, so redelivery after a crash at any point converges:
    commit (atomic: event + observations + export intents) -> enqueue exports -> mark enqueued."""
    p = PointerMessage.from_json(body)
    received_at = datetime.fromisoformat(p.received_at)
    common = dict(
        tenant_id=p.tenant_id, client_id=p.client_id, ingest_id=p.ingest_id, source=p.source,
        idempotency_key=p.idempotency_key, raw_key=p.s3_key, raw_sha256=p.sha256,
        received_at=received_at,
    )  # fmt: skip

    raw = store.get(p.s3_key)
    if hashlib.sha256(raw).hexdigest() != p.sha256:
        repo.quarantine(**common)
        raise PoisonMessage("checksum mismatch")
    try:
        parsed = parse_payload(p.source, raw)
    except (hl7.Hl7Error, ValidationError, ValueError, UnicodeDecodeError):
        repo.quarantine(**common)
        raise PoisonMessage("unparseable payload") from None

    result = repo.commit_ingest(
        **common,
        pseudonym=parsed.pseudonym,
        device_external_id=parsed.device_external_id,
        observations=parsed.observations,
    )
    for ref in result.pending_exports:
        export_queue.send(ExportPointer(ref.export_id, p.tenant_id, p.trace_id).to_json())
    repo.mark_export_enqueued(p.tenant_id, [r.export_id for r in result.pending_exports])
    return "duplicate" if result.duplicate else "processed"
