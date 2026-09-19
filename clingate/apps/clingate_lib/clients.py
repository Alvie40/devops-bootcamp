from __future__ import annotations

import json
from pathlib import Path

from .model import Client


class StaticClientRegistry:
    """Maps an authenticated caller (Cognito app client id, or mTLS cert fingerprint) to a
    tenant. Dev/test implementation backed by a JSON file; in AWS this is the `clients` table."""

    def __init__(self, clients: list[Client]) -> None:
        self._by_id = {c.client_id: c for c in clients}
        self._by_cert = {c.cert_sha256: c for c in clients if c.cert_sha256}

    @classmethod
    def from_file(cls, path: str | Path) -> StaticClientRegistry:
        return cls([Client(**c) for c in json.loads(Path(path).read_text())])

    def by_client_id(self, client_id: str) -> Client | None:
        c = self._by_id.get(client_id)
        return c if c and c.enabled else None

    def by_cert(self, sha256_hex: str | None) -> Client | None:
        if not sha256_hex:
            return None
        c = self._by_cert.get(sha256_hex)
        return c if c and c.enabled else None
