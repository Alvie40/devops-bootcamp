from __future__ import annotations

import logging
from datetime import UTC, datetime

from clingate_lib import hl7
from clingate_lib.ids import outbound_control_id
from clingate_lib.mllp import MllpError
from clingate_lib.model import ExportPointer, PoisonMessage, RetryableError
from clingate_lib.repo import Repository

from .pool import DestinationPool

log = logging.getLogger("hl7_exporter")


async def process_export(
    body: str, *, repo: Repository, pool: DestinationPool, processing_id: str
) -> str:
    """ACK handling: AA -> acked. AE (or transport failure / open circuit) -> retry with
    backoff (redelivery). AR -> failed, do not retry (DLQ)."""
    p = ExportPointer.from_json(body)
    job = repo.load_export(p.tenant_id, p.export_id)
    if job is None:
        raise PoisonMessage("export not found")
    if job.status == "acked":
        return "already-acked"
    d = job.destination
    message = hl7.build_oru(
        control_id=outbound_control_id(job.ingest_event_id, d.id),
        sending_app=d.sending_app,
        sending_facility=d.sending_facility,
        receiving_app=d.receiving_app,
        receiving_facility=d.receiving_facility,
        processing_id=processing_id,
        pseudonym=job.pseudonym,
        observations=job.observations,
        timestamp=datetime.now(UTC),
    )
    try:
        raw_ack = await pool.send(d, message.encode("utf-8"))
        ack = hl7.parse_ack(hl7.decode_bytes(raw_ack))
    except (MllpError, hl7.Hl7Error, OSError, RetryableError) as e:
        if not isinstance(e, RetryableError):
            repo.record_export_attempt(p.tenant_id, p.export_id, ack_code=None, status="pending")
        raise RetryableError("destination unavailable") from None

    if ack.code in ("AA", "CA"):
        repo.record_export_attempt(p.tenant_id, p.export_id, ack_code=ack.code, status="acked")
        return "acked"
    if ack.code in ("AE", "CE"):
        repo.record_export_attempt(p.tenant_id, p.export_id, ack_code=ack.code, status="pending")
        raise RetryableError("destination reported a transient error")
    repo.record_export_attempt(p.tenant_id, p.export_id, ack_code=ack.code, status="failed")
    raise PoisonMessage("destination rejected the message")
