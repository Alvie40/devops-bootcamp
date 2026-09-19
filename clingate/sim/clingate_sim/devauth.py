"""Dev/test auth: a throwaway RSA keypair, its JWKS, and Cognito-shaped access tokens."""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ISSUER = "https://dev.clingate.local"
KID = "dev-key-1"


def _b64(n: int) -> str:
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


class DevKeys:
    def __init__(self, private_key: rsa.RSAPrivateKey) -> None:
        self.private_key = private_key

    @classmethod
    def generate(cls) -> DevKeys:
        return cls(rsa.generate_private_key(public_exponent=65537, key_size=2048))

    @classmethod
    def load_or_create(cls, directory: str | Path) -> DevKeys:
        d = Path(directory)
        pem = d / "private.pem"
        if pem.exists():
            return cls(serialization.load_pem_private_key(pem.read_bytes(), password=None))
        keys = cls.generate()
        d.mkdir(parents=True, exist_ok=True)
        pem.write_bytes(
            keys.private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        (d / "jwks.json").write_text(json.dumps(keys.jwks()))
        return keys

    @property
    def public_key(self):
        return self.private_key.public_key()

    def jwks(self) -> dict:
        n = self.public_key.public_numbers()
        return {"keys": [{"kty": "RSA", "alg": "RS256", "use": "sig", "kid": KID,
                          "n": _b64(n.n), "e": _b64(n.e)}]}  # fmt: skip

    def mint(
        self,
        client_id: str,
        scope: str = "ingest:write",
        *,
        ttl: int = 3600,
        issuer: str = ISSUER,
        now: float | None = None,
    ) -> str:
        t = int(now if now is not None else time.time())
        payload = {"iss": issuer, "client_id": client_id, "scope": scope, "token_use": "access",
                   "iat": t, "exp": t + ttl}  # fmt: skip
        return jwt.encode(payload, self.private_key, algorithm="RS256", headers={"kid": KID})


if __name__ == "__main__":
    import sys

    keys = DevKeys.load_or_create("dev/.keys")
    client = sys.argv[1] if len(sys.argv) > 1 else "dev-device-client"
    print(keys.mint(client, ttl=int(sys.argv[2]) if len(sys.argv) > 2 else 86400))
