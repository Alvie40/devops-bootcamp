from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class QueueMessage:
    body: str
    receipt: str
    receive_count: int = 1


class RawStore(Protocol):
    def put_if_absent(self, key: str, data: bytes, sha256_hex: str) -> bool:
        """True if created, False if the key already existed. Raw objects are immutable."""
        ...

    def get(self, key: str) -> bytes: ...

    def exists(self, key: str) -> bool: ...


class WorkQueue(Protocol):
    def send(self, body: str) -> None: ...

    def receive(self, max_messages: int = 10, wait_seconds: int = 20) -> list[QueueMessage]: ...

    def delete(self, msg: QueueMessage) -> None: ...

    def change_visibility(self, msg: QueueMessage, seconds: int) -> None: ...
