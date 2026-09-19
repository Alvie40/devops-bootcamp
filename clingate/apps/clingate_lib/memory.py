"""In-memory RawStore/WorkQueue: unit tests, and single-process runs with no docker."""

from __future__ import annotations

import itertools
import threading

from .ports import QueueMessage


class MemoryRawStore:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.fail_on_put = False
        self._lock = threading.Lock()

    def put_if_absent(self, key: str, data: bytes, sha256_hex: str) -> bool:
        if self.fail_on_put:
            raise OSError("simulated store failure")
        with self._lock:
            if key in self.objects:
                return False
            self.objects[key] = data
            return True

    def get(self, key: str) -> bytes:
        return self.objects[key]

    def exists(self, key: str) -> bool:
        return key in self.objects


class MemoryQueue:
    def __init__(self) -> None:
        self._available: list[tuple[str, int]] = []
        self._inflight: dict[str, tuple[str, int]] = {}
        self._ids = itertools.count(1)
        self._lock = threading.Lock()
        self.fail_on_send = False
        self.sent: list[str] = []

    def send(self, body: str) -> None:
        if self.fail_on_send:
            raise OSError("simulated queue failure")
        with self._lock:
            self._available.append((body, 0))
            self.sent.append(body)

    def receive(self, max_messages: int = 10, wait_seconds: int = 20) -> list[QueueMessage]:
        with self._lock:
            batch, self._available = self._available[:max_messages], self._available[max_messages:]
            out = []
            for body, count in batch:
                receipt = str(next(self._ids))
                self._inflight[receipt] = (body, count + 1)
                out.append(QueueMessage(body=body, receipt=receipt, receive_count=count + 1))
            return out

    def delete(self, msg: QueueMessage) -> None:
        with self._lock:
            self._inflight.pop(msg.receipt, None)

    def change_visibility(self, msg: QueueMessage, seconds: int) -> None:
        # Tests model "visibility timeout expired" by making the message available again.
        with self._lock:
            entry = self._inflight.pop(msg.receipt, None)
            if entry is not None:
                self._available.append(entry)

    def depth(self) -> int:
        with self._lock:
            return len(self._available)

    def inflight(self) -> int:
        with self._lock:
            return len(self._inflight)


class NullRawStore:
    """Baseline only (CLINGATE_BACKEND=null): discards writes so a load run measures the API's
    own CPU cost (hypothesis 5) without unbounded memory growth. Never for real use."""

    def put_if_absent(self, key: str, data: bytes, sha256_hex: str) -> bool:
        return True

    def get(self, key: str) -> bytes:
        raise KeyError(key)

    def exists(self, key: str) -> bool:
        return False


class NullQueue:
    def send(self, body: str) -> None:
        return None

    def receive(self, max_messages: int = 10, wait_seconds: int = 20) -> list[QueueMessage]:
        return []

    def delete(self, msg: QueueMessage) -> None:
        return None

    def change_visibility(self, msg: QueueMessage, seconds: int) -> None:
        return None
