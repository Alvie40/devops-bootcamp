"""boto3 adapters. Point them at LocalStack with AWS_ENDPOINT_URL for dev."""

from __future__ import annotations

import base64
import hashlib

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from .ports import QueueMessage

_CFG = Config(retries={"max_attempts": 3, "mode": "standard"}, connect_timeout=2, read_timeout=5)


class S3RawStore:
    def __init__(self, bucket: str, *, kms_key_id: str | None = None, client=None) -> None:
        self._bucket = bucket
        self._kms = kms_key_id
        self._s3 = client or boto3.client("s3", config=_CFG)

    def put_if_absent(self, key: str, data: bytes, sha256_hex: str) -> bool:
        extra: dict[str, str] = {}
        if self._kms:
            extra = {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": self._kms}
        checksum = base64.b64encode(bytes.fromhex(sha256_hex)).decode()
        try:
            self._s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ChecksumSHA256=checksum,
                IfNoneMatch="*",
                **extra,
            )
        except ClientError as e:
            if e.response["Error"]["Code"] in ("PreconditionFailed", "412"):
                return False
            raise
        return True

    def get(self, key: str) -> bytes:
        return self._s3.get_object(Bucket=self._bucket, Key=key)["Body"].read()

    def exists(self, key: str) -> bool:
        try:
            self._s3.head_object(Bucket=self._bucket, Key=key)
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
                return False
            raise
        return True


class SqsQueue:
    def __init__(self, queue_url: str, *, client=None) -> None:
        self._url = queue_url
        self._sqs = client or boto3.client("sqs", config=_CFG)

    def send(self, body: str) -> None:
        self._sqs.send_message(QueueUrl=self._url, MessageBody=body)

    def receive(self, max_messages: int = 10, wait_seconds: int = 20) -> list[QueueMessage]:
        resp = self._sqs.receive_message(
            QueueUrl=self._url,
            MaxNumberOfMessages=min(max_messages, 10),
            WaitTimeSeconds=wait_seconds,
            AttributeNames=["ApproximateReceiveCount"],
        )
        return [
            QueueMessage(
                body=m["Body"],
                receipt=m["ReceiptHandle"],
                receive_count=int(m["Attributes"]["ApproximateReceiveCount"]),
            )
            for m in resp.get("Messages", [])
        ]

    def delete(self, msg: QueueMessage) -> None:
        self._sqs.delete_message(QueueUrl=self._url, ReceiptHandle=msg.receipt)

    def change_visibility(self, msg: QueueMessage, seconds: int) -> None:
        self._sqs.change_message_visibility(
            QueueUrl=self._url, ReceiptHandle=msg.receipt, VisibilityTimeout=seconds
        )


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
