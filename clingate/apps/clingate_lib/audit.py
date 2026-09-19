from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Protocol


@dataclass(frozen=True)
class AuditEvent:
    actor_type: str
    actor_id: str
    action: str
    outcome: str
    tenant_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    subject_pseudonym: str | None = None
    purpose: str | None = None
    request_id: str | None = None
    source_ip: str | None = None
    ts: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class AuditSink(Protocol):
    def emit(self, event: AuditEvent) -> None: ...


class LogAuditSink:
    """One JSON line per event on the dedicated `clingate.audit` logger. In AWS that
    stream is shipped to CloudWatch Logs and on to the out-of-account archive."""

    def __init__(self) -> None:
        self._log = logging.getLogger("clingate.audit")

    def emit(self, event: AuditEvent) -> None:
        self._log.info(json.dumps(asdict(event)))


class MemoryAuditSink:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def emit(self, event: AuditEvent) -> None:
        self.events.append(event)
