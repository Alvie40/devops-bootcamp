from __future__ import annotations

import asyncio
import ssl
import time
from collections.abc import Callable

from clingate_lib.mllp import MllpClient, MllpError
from clingate_lib.model import RetryableError
from clingate_lib.repo import Destination


class CircuitOpenError(RetryableError):
    pass


class CircuitBreaker:
    """Opens after `threshold` consecutive failures; half-opens after `reset_after` seconds."""

    def __init__(
        self,
        threshold: int = 5,
        reset_after: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.threshold, self.reset_after, self._clock = threshold, reset_after, clock
        self._failures = 0
        self._opened_at: float | None = None

    def allow(self) -> bool:
        if self._opened_at is None:
            return True
        return self._clock() - self._opened_at >= self.reset_after

    def success(self) -> None:
        self._failures, self._opened_at = 0, None

    def failure(self) -> None:
        self._failures += 1
        if self._failures >= self.threshold:
            self._opened_at = self._clock()


class DestinationPool:
    """Per-destination connection pool. `max_connections` is the destination's concurrency
    budget: scaling exporter pods must never exceed what the far end can accept."""

    def __init__(
        self,
        *,
        ssl_factory: Callable[[Destination], ssl.SSLContext | None] = lambda d: None,
        timeout: float = 10.0,
    ) -> None:
        self._ssl_factory = ssl_factory
        self._timeout = timeout
        self._sems: dict[str, asyncio.Semaphore] = {}
        self._idle: dict[str, list[MllpClient]] = {}
        self._breakers: dict[str, CircuitBreaker] = {}

    async def send(self, dest: Destination, payload: bytes) -> bytes:
        breaker = self._breakers.setdefault(dest.id, CircuitBreaker())
        if not breaker.allow():
            raise CircuitOpenError("circuit open")
        sem = self._sems.setdefault(dest.id, asyncio.Semaphore(dest.max_connections))
        async with sem:
            idle = self._idle.setdefault(dest.id, [])
            client = (
                idle.pop()
                if idle
                else MllpClient(
                    dest.host, dest.port, ssl_context=self._ssl_factory(dest), timeout=self._timeout
                )
            )
            try:
                response = await client.send(payload)
            except MllpError:
                breaker.failure()
                await client.close()
                raise
            breaker.success()
            idle.append(client)
            return response

    async def close(self) -> None:
        for clients in self._idle.values():
            for c in clients:
                await c.close()
