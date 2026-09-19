from __future__ import annotations

import os

import uvicorn

from clingate_lib.audit import LogAuditSink
from clingate_lib.clients import StaticClientRegistry
from clingate_lib.config import Settings
from clingate_lib.logging import configure
from clingate_lib.wiring import build_queue, build_store

from .app import create_app
from .auth import JwtVerifier, file_key_resolver, jwks_key_resolver


def main() -> None:
    configure("ingest_api")
    s = Settings.from_env()
    jwks_file = os.environ.get("CLINGATE_JWKS_FILE")  # dev/baseline only
    resolver = (
        file_key_resolver(jwks_file)
        if jwks_file
        else jwks_key_resolver(os.environ["CLINGATE_JWKS_URL"])  # https URL (Cognito)
    )
    verifier = JwtVerifier(key_resolver=resolver, issuer=os.environ["CLINGATE_JWT_ISSUER"])
    app = create_app(
        verifier=verifier,
        registry=StaticClientRegistry.from_file(s.clients_file),
        store=build_store(s),
        queue=build_queue(s, s.ingest_queue_url),
        audit=LogAuditSink(),
    )
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), log_config=None)  # noqa: S104


if __name__ == "__main__":
    main()
