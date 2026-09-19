from __future__ import annotations

import asyncio
import os
import ssl

from clingate_lib.audit import LogAuditSink
from clingate_lib.clients import StaticClientRegistry
from clingate_lib.config import Settings
from clingate_lib.logging import configure
from clingate_lib.mllp import serve
from clingate_lib.wiring import build_queue, build_store

from .app import Listener


def _tls() -> ssl.SSLContext | None:
    cert, key, ca = (
        os.environ.get(k) for k in ("CLINGATE_TLS_CERT", "CLINGATE_TLS_KEY", "CLINGATE_TLS_CA")
    )
    if not (cert and key and ca):
        return None
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(cert, key)
    ctx.load_verify_locations(ca)
    ctx.verify_mode = ssl.CERT_REQUIRED  # mutual TLS: the client cert is the sender identity
    return ctx


async def main() -> None:
    log = configure("mllp_listener")
    s = Settings.from_env()
    ctx = _tls()
    dev_client = os.environ.get("CLINGATE_DEV_CLIENT")
    if ctx is None:
        log.warning("running WITHOUT TLS: dev only", extra={"ctx": {"reason": "no_tls"}})
    listener = Listener(
        registry=StaticClientRegistry.from_file(s.clients_file),
        store=build_store(s),
        queue=build_queue(s, s.ingest_queue_url),
        audit=LogAuditSink(),
        processing_id=s.processing_id,
        dev_client_id=dev_client if ctx is None else None,
    )
    server = await serve(
        listener.handle,
        "0.0.0.0",  # noqa: S104
        int(os.environ.get("PORT", "2575")),
        ssl_context=ctx,
    )
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
