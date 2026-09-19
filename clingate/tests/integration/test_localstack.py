"""Needs LocalStack (`make dev-up-aws`, AWS_ENDPOINT_URL set). Covers what moto cannot:
S3 checksum enforcement and the SQS redrive-to-DLQ policy the design relies on for poison messages."""

from __future__ import annotations

import os
import uuid

import boto3
import pytest

from clingate_lib.aws import S3RawStore, SqsQueue, sha256_hex

ENDPOINT = os.environ.get("AWS_ENDPOINT_URL")
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not ENDPOINT, reason="AWS_ENDPOINT_URL not set (LocalStack)"),
]
BASE = (ENDPOINT or "").rstrip("/") + "/000000000000"


def test_s3_put_if_absent_is_immutable():
    store = S3RawStore("clingate-raw-dev")
    key = f"raw/test/{uuid.uuid4().hex}"
    assert store.put_if_absent(key, b"first", sha256_hex(b"first")) is True
    assert store.put_if_absent(key, b"second", sha256_hex(b"second")) is False
    assert store.get(key) == b"first"


def test_s3_rejects_body_that_does_not_match_declared_checksum():
    store = S3RawStore("clingate-raw-dev")
    with pytest.raises(Exception, match=r"(?i)checksum|BadDigest|Invalid"):
        store.put_if_absent(f"raw/test/{uuid.uuid4().hex}", b"payload", sha256_hex(b"other"))


def test_poison_message_lands_in_dlq_after_max_receive_count():
    ingest, dlq = SqsQueue(f"{BASE}/clingate-ingest"), SqsQueue(f"{BASE}/clingate-ingest-dlq")
    marker = f'{{"poison":"{uuid.uuid4().hex}"}}'
    ingest.send(marker)
    for _ in range(5):  # maxReceiveCount = 5: receive and never delete
        [m] = ingest.receive(wait_seconds=1)
        assert m.body == marker
        ingest.change_visibility(m, 0)
    assert ingest.receive(wait_seconds=1) == []  # moved out of the source queue
    found = [m.body for m in dlq.receive(max_messages=10, wait_seconds=2)]
    assert marker in found


def test_s3_client_sees_the_configured_endpoint():
    assert boto3.client("s3").meta.endpoint_url.startswith(ENDPOINT)
