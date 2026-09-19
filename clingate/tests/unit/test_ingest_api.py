from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from clingate_lib.ids import raw_key
from clingate_lib.model import PointerMessage
from clingate_sim.generate import device_batch
from ingest_api.app import create_app
from ingest_api.auth import JwtVerifier
from tests.conftest import TENANT_A


@pytest.fixture
def client(keys, issuer, registry, store, queue, audit):
    verifier = JwtVerifier(key_resolver=lambda _t: keys.public_key, issuer=issuer)
    app = create_app(verifier=verifier, registry=registry, store=store, queue=queue, audit=audit)
    return TestClient(app)


def _post(
    client,
    keys,
    *,
    body=None,
    idem=None,
    token="auto",
    scope="ingest:write",
    cid="dev-device-client",
):
    key, raw = device_batch(1, 1)
    headers = {"Idempotency-Key": idem or key, "Content-Type": "application/json"}
    if token == "auto":
        token = keys.mint(cid, scope)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return (
        client.post("/v1/batches", content=raw if body is None else body, headers=headers),
        key,
        raw,
    )


def test_FR3_accepted_is_durable_and_enqueued(client, keys, store, queue):
    r, key, raw = _post(client, keys)
    assert r.status_code == 202 and r.json()["duplicate"] is False
    assert store.objects[raw_key(TENANT_A, "http", key)] == raw  # stored BEFORE the 202
    pointer = PointerMessage.from_json(queue.sent[0])
    assert pointer.s3_key == raw_key(TENANT_A, "http", key)
    assert pointer.ingest_id == r.json()["ingest_id"]


def test_queue_message_is_a_pointer_without_payload(client, keys, queue):
    _post(client, keys)
    assert "8867-4" not in queue.sent[0] and "observations" not in queue.sent[0]


def test_FR4_duplicate_is_accepted_and_not_rewritten(client, keys, store, queue):
    _post(client, keys)
    r, _, _ = _post(client, keys)
    assert r.status_code == 202 and r.json()["duplicate"] is True
    assert len(store.objects) == 1 and len(queue.sent) == 2  # re-enqueue is harmless


@pytest.mark.parametrize(
    ("kw", "status"),
    [
        ({"token": None}, 401),
        ({"token": "not-a-jwt"}, 401),
        ({"scope": "records:read"}, 403),
        ({"cid": "unknown-client"}, 403),
        ({"cid": "disabled-client"}, 403),
        ({"cid": "lab-a"}, 403),  # wrong client kind
    ],
)
def test_authn_authz(client, keys, kw, status):
    r, _, _ = _post(client, keys, **kw)
    assert r.status_code == status


def test_expired_token_rejected(client, keys):
    r, _, _ = _post(client, keys, token=keys.mint("dev-device-client", ttl=-3600))
    assert r.status_code == 401


def test_wrong_issuer_rejected(client, keys):
    r, _, _ = _post(client, keys, token=keys.mint("dev-device-client", issuer="https://evil"))
    assert r.status_code == 401


def test_token_signed_by_other_key_rejected(client, keys):
    from clingate_sim.devauth import DevKeys

    r, _, _ = _post(client, keys, token=DevKeys.generate().mint("dev-device-client"))
    assert r.status_code == 401


def test_idempotency_key_must_match_batch_id(client, keys):
    r, _, _ = _post(client, keys, idem="different-key-1234")
    assert r.status_code == 422 and r.json()["error"] == "idempotency_key_mismatch"


def test_missing_idempotency_key(client, keys):
    _, raw = device_batch(1, 2)
    r = client.post(
        "/v1/batches",
        content=raw,
        headers={"Authorization": f"Bearer {keys.mint('dev-device-client')}"},
    )
    assert r.status_code == 422


def test_invalid_payload_error_never_echoes_values(client, keys):
    key, raw = device_batch(1, 3)
    bad = json.loads(raw)
    bad["subject_ref"] = "SECRET VALUE WITH SPACES"
    r, _, _ = _post(client, keys, body=json.dumps(bad), idem=key)
    assert r.status_code == 422
    assert "SECRET" not in r.text
    assert r.json()["detail"][0]["loc"] == ["subject_ref"]


def test_extra_fields_forbidden(client, keys):
    key, raw = device_batch(1, 4)
    bad = json.loads(raw)
    bad["patient_name"] = "x"
    r, _, _ = _post(client, keys, body=json.dumps(bad), idem=key)
    assert r.status_code == 422


def test_payload_too_large(client, keys):
    r, _, _ = _post(client, keys, body=b"x" * (1024 * 1024 + 1))
    assert r.status_code == 413


def test_H1_store_failure_is_503_and_nothing_acknowledged(client, keys, store, queue):
    store.fail_on_put = True
    r, _, _ = _post(client, keys)
    assert r.status_code == 503 and not queue.sent


def test_H1_queue_failure_is_503(client, keys, queue):
    queue.fail_on_send = True
    r, _, _ = _post(client, keys)
    assert r.status_code == 503


def test_audit_event_emitted_without_payload(client, keys, audit):
    _post(client, keys)
    ev = audit.events[0]
    assert (ev.action, ev.outcome, ev.actor_id) == (
        "ingest.batch.accept",
        "accepted",
        "dev-device-client",
    )
    assert "8867-4" not in json.dumps(ev.__dict__)


def test_security_headers_and_docs_disabled(client):
    r = client.get("/healthz")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["cross-origin-resource-policy"] == "same-origin"
    assert r.headers["cache-control"] == "no-store"
    assert client.get("/docs").status_code == 404 and client.get("/openapi.json").status_code == 404


def test_file_key_resolver_verifies_and_rejects_unknown_kid(tmp_path, keys, issuer):
    import json

    import jwt

    from ingest_api.auth import AuthError, file_key_resolver

    path = tmp_path / "jwks.json"
    path.write_text(json.dumps(keys.jwks()))
    verifier = JwtVerifier(key_resolver=file_key_resolver(str(path)), issuer=issuer)
    assert verifier.verify(keys.mint("dev-device-client")).client_id == "dev-device-client"
    forged = jwt.encode({"iss": issuer, "exp": 9999999999, "client_id": "x"}, keys.private_key,
                        algorithm="RS256", headers={"kid": "other"})  # fmt: skip
    with pytest.raises(AuthError):
        verifier.verify(forged)
