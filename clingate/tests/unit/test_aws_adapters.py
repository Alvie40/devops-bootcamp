from __future__ import annotations

import boto3
import pytest
from moto import mock_aws

from clingate_lib.aws import S3RawStore, SqsQueue, sha256_hex


@pytest.fixture(autouse=True)
def _aws_env(monkeypatch):
    for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.setenv(k, "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)


@mock_aws
def test_s3_put_if_absent_is_immutable():
    boto3.client("s3").create_bucket(Bucket="raw")
    store = S3RawStore("raw")
    data = b"payload"
    assert store.put_if_absent("k1", data, sha256_hex(data)) is True
    assert store.put_if_absent("k1", b"DIFFERENT", sha256_hex(b"DIFFERENT")) is False
    assert store.get("k1") == data  # first write wins; raw is immutable
    assert store.exists("k1") and not store.exists("nope")


@mock_aws
def test_sqs_roundtrip_and_receive_count():
    url = boto3.client("sqs").create_queue(QueueName="q")["QueueUrl"]
    q = SqsQueue(url)
    q.send('{"a":1}')
    [m] = q.receive(wait_seconds=0)
    assert m.body == '{"a":1}' and m.receive_count == 1
    q.change_visibility(m, 0)
    [m2] = q.receive(wait_seconds=0)
    assert m2.receive_count == 2
    q.delete(m2)
    assert q.receive(wait_seconds=0) == []
