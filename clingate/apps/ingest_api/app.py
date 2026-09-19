from __future__ import annotations

import hashlib
import logging
import re
import uuid
from datetime import UTC, datetime

import anyio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from clingate_lib.audit import AuditEvent, AuditSink
from clingate_lib.clients import StaticClientRegistry
from clingate_lib.ids import ingest_id, raw_key
from clingate_lib.model import PointerMessage
from clingate_lib.ports import RawStore, WorkQueue
from clingate_lib.schemas import BatchIn

from .auth import AuthError, JwtVerifier

log = logging.getLogger("ingest_api")
_IDEM = re.compile(r"^[A-Za-z0-9._-]{8,128}$")
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "no-store",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


class _ApiError(Exception):
    def __init__(self, status: int, code: str, detail: list | None = None) -> None:
        self.status, self.code, self.detail = status, code, detail


def create_app(
    *,
    verifier: JwtVerifier,
    registry: StaticClientRegistry,
    store: RawStore,
    queue: WorkQueue,
    audit: AuditSink,
    max_body: int = 1024 * 1024,
) -> FastAPI:
    app = FastAPI(title="clingate ingest-api", docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def headers(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        for k, v in SECURITY_HEADERS.items():
            response.headers[k] = v
        return response

    @app.exception_handler(_ApiError)
    async def api_error(_: Request, exc: _ApiError) -> JSONResponse:
        body: dict = {"error": exc.code}
        if exc.detail is not None:
            body["detail"] = exc.detail
        return JSONResponse(body, status_code=exc.status)

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz() -> dict:
        return {"status": "ok"}

    async def read_limited(request: Request) -> bytes:
        declared = request.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > max_body:
            raise _ApiError(413, "payload_too_large")
        chunks, size = [], 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > max_body:
                raise _ApiError(413, "payload_too_large")
            chunks.append(chunk)
        return b"".join(chunks)

    def handle(auth_header: str | None, idem: str | None, body: bytes, request_id: str) -> dict:
        if not auth_header or not auth_header.startswith("Bearer "):
            raise _ApiError(401, "unauthorized")
        try:
            claims = verifier.verify(auth_header[7:])
        except AuthError:
            raise _ApiError(401, "unauthorized") from None
        client = registry.by_client_id(claims.client_id)
        if client is None or client.kind != "http" or "ingest:write" not in claims.scopes:
            raise _ApiError(403, "forbidden")
        if not idem or not _IDEM.match(idem):
            raise _ApiError(422, "invalid_idempotency_key")
        try:
            batch = BatchIn.model_validate_json(body)
        except ValidationError as e:
            # Locations and error types only: pydantic messages can echo submitted values.
            detail = [{"loc": list(x["loc"]), "type": x["type"]} for x in e.errors()]
            raise _ApiError(422, "invalid_payload", detail) from None
        if batch.batch_id != idem:
            raise _ApiError(422, "idempotency_key_mismatch")

        sha = hashlib.sha256(body).hexdigest()
        key = raw_key(client.tenant_id, "http", idem)
        try:
            created = store.put_if_absent(key, body, sha)
            received_at = datetime.now(UTC)
            pointer = PointerMessage(
                ingest_id=ingest_id(client.tenant_id, "http", idem),
                tenant_id=client.tenant_id,
                client_id=client.client_id,
                source="http",
                idempotency_key=idem,
                s3_key=key,
                sha256=sha,
                received_at=received_at.isoformat(),
                trace_id=request_id,
            )
            # Enqueue even for a duplicate: it is harmless (the worker is idempotent) and it
            # covers a first attempt that stored the object but failed to enqueue.
            queue.send(pointer.to_json())
        except Exception:
            log.error(
                "durable path failed", exc_info=True, extra={"ctx": {"request_id": request_id}}
            )
            raise _ApiError(503, "unavailable") from None

        audit.emit(
            AuditEvent(
                actor_type="client",
                actor_id=client.client_id,
                tenant_id=client.tenant_id,
                action="ingest.batch.accept",
                resource_type="ingest_event",
                resource_id=pointer.ingest_id,
                outcome="accepted" if created else "duplicate",
                request_id=request_id,
            )
        )
        return {"ingest_id": pointer.ingest_id, "status": "accepted", "duplicate": not created}

    @app.post("/v1/batches", status_code=202)
    async def post_batch(request: Request) -> dict:
        body = await read_limited(request)
        return await anyio.to_thread.run_sync(
            handle,
            request.headers.get("authorization"),
            request.headers.get("idempotency-key"),
            body,
            request.state.request_id,
        )

    return app
