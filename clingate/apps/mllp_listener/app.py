from __future__ import annotations

import asyncio
import hashlib
import logging
import uuid
from datetime import UTC, datetime

from clingate_lib import hl7
from clingate_lib.audit import AuditEvent, AuditSink
from clingate_lib.clients import StaticClientRegistry
from clingate_lib.ids import ingest_id, raw_key
from clingate_lib.mllp import PeerInfo
from clingate_lib.model import PointerMessage
from clingate_lib.ports import RawStore, WorkQueue

log = logging.getLogger("mllp_listener")


class Listener:
    """ACK policy: AA only after the (minimised) raw message is durable AND enqueued.
    AE = our side failed, sender should retry. AR = message/sender rejected, do not retry."""

    def __init__(
        self,
        *,
        registry: StaticClientRegistry,
        store: RawStore,
        queue: WorkQueue,
        audit: AuditSink,
        processing_id: str,
        dev_client_id: str | None = None,
    ) -> None:
        self._registry = registry
        self._store, self._queue, self._audit = store, queue, audit
        self._processing_id = processing_id
        self._dev_client_id = dev_client_id  # dev only: plain TCP, no client cert

    def _ack(
        self, msh: hl7.Msh | None, code: str, text: str | None = None, err: str = "207"
    ) -> bytes:
        cid = "ACK" + uuid.uuid4().hex[:16]
        return hl7.build_ack(msh, code, control_id=cid, text=text, error_code=err).encode("utf-8")

    async def handle(self, frame: bytes, peer: PeerInfo) -> bytes:
        request_id = uuid.uuid4().hex
        client = (
            self._registry.by_cert(peer.cert_sha256)
            if peer.cert_sha256
            else (self._registry.by_client_id(self._dev_client_id) if self._dev_client_id else None)
        )
        try:
            text = hl7.decode_bytes(frame)
        except hl7.Hl7Error as e:
            return self._ack(None, "AR", e.text, e.code)
        msh = hl7.parse_msh_lenient(text)
        if client is None or client.kind != "mllp":
            log.warning("unknown sender", extra={"ctx": {"request_id": request_id}})
            return self._ack(msh, "AR", "sender not authorized", "204")
        try:
            parsed = hl7.parse_oru(text)
        except hl7.Hl7Error as e:
            self._emit(client.tenant_id, client.client_id, "rejected", request_id, None)
            return self._ack(msh, "AR", e.text, e.code)
        m = parsed.msh
        if (client.sending_facility and m.sending_facility != client.sending_facility) or (
            client.sending_application and m.sending_app != client.sending_application
        ):
            self._emit(client.tenant_id, client.client_id, "rejected", request_id, None)
            return self._ack(msh, "AR", "sender identity mismatch", "204")
        if m.processing_id != self._processing_id:
            return self._ack(msh, "AR", "unsupported processing id", "202")

        scrubbed, dropped = hl7.scrub_identifiers(text)
        data = scrubbed.encode("utf-8")
        sha = hashlib.sha256(data).hexdigest()
        key = raw_key(client.tenant_id, "mllp", m.control_id)
        try:
            created = await asyncio.to_thread(self._store.put_if_absent, key, data, sha)
            pointer = PointerMessage(
                ingest_id=ingest_id(client.tenant_id, "mllp", m.control_id),
                tenant_id=client.tenant_id,
                client_id=client.client_id,
                source="mllp",
                idempotency_key=m.control_id,
                s3_key=key,
                sha256=sha,
                received_at=datetime.now(UTC).isoformat(),
                trace_id=request_id,
            )
            await asyncio.to_thread(self._queue.send, pointer.to_json())
        except Exception:
            log.error(
                "durable path failed", exc_info=True, extra={"ctx": {"request_id": request_id}}
            )
            self._emit(client.tenant_id, client.client_id, "error", request_id, None)
            return self._ack(msh, "AE", "temporarily unable to store message", "207")

        log.info(
            "accepted",
            extra={"ctx": {"request_id": request_id, "tenant_id": client.tenant_id,
                           "source": "mllp", "dropped_phi_fields": dropped}},
        )  # fmt: skip
        self._emit(
            client.tenant_id, client.client_id, "accepted" if created else "duplicate",
            request_id, pointer.ingest_id,
        )  # fmt: skip
        return self._ack(msh, "AA")

    def _emit(
        self, tenant: str, client: str, outcome: str, request_id: str, ingest: str | None
    ) -> None:
        self._audit.emit(
            AuditEvent(
                actor_type="client", actor_id=client, tenant_id=tenant,
                action="ingest.hl7.receive", resource_type="ingest_event",
                resource_id=ingest, outcome=outcome, request_id=request_id,
            )
        )  # fmt: skip
