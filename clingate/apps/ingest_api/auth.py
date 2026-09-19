from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple

import jwt


class AuthError(Exception):
    pass


class TokenClaims(NamedTuple):
    client_id: str
    scopes: frozenset[str]


class JwtVerifier:
    """Verifies Cognito-style access tokens (RS256, `client_id` + space-delimited `scope`).

    `key_resolver` maps a raw token to its public key. In AWS it wraps a cached JWKS client, so
    a Cognito call happens only on key rotation, never per request.
    """

    def __init__(
        self, *, key_resolver: Callable[[str], Any], issuer: str, leeway: int = 30
    ) -> None:
        self._resolve = key_resolver
        self._issuer = issuer
        self._leeway = leeway

    def verify(self, token: str) -> TokenClaims:
        try:
            claims = jwt.decode(
                token,
                self._resolve(token),
                algorithms=["RS256"],
                issuer=self._issuer,
                leeway=self._leeway,
                options={"require": ["exp", "iss"], "verify_aud": False},
            )
        except (jwt.PyJWTError, ValueError, OSError) as e:
            raise AuthError("invalid token") from e
        client_id = claims.get("client_id")
        if not isinstance(client_id, str) or not client_id:
            raise AuthError("missing client_id")
        return TokenClaims(client_id, frozenset(str(claims.get("scope", "")).split()))


def jwks_key_resolver(jwks_url: str) -> Callable[[str], Any]:
    client = jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)
    return lambda token: client.get_signing_key_from_jwt(token).key


def file_key_resolver(path: str) -> Callable[[str], Any]:
    """Dev/baseline only: keys from a local JWKS file, selected by the token's `kid`.
    (PyJWT refuses file:// URLs on purpose; production uses jwks_key_resolver over https.)"""
    keys = {k.key_id: k.key for k in jwt.PyJWKSet.from_json(open(path).read()).keys}  # noqa: SIM115

    def resolve(token: str) -> Any:
        kid = jwt.get_unverified_header(token).get("kid")
        if kid not in keys:
            raise ValueError("unknown kid")
        return keys[kid]

    return resolve
