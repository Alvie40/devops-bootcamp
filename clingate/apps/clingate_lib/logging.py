"""PHI-safe JSON logging: fields are allow-listed, exception messages are never emitted."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime

ALLOWED_FIELDS = frozenset(
    {
        "request_id", "trace_id", "tenant_id", "client_id", "source", "ingest_id",
        "export_id", "action", "outcome", "status", "code", "duration_ms", "count",
        "destination_id", "attempt", "queue", "component", "reason", "dropped_phi_fields",
    }
)  # fmt: skip


class SafeJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        ctx = getattr(record, "ctx", None) or {}
        dropped = []
        for key, value in ctx.items():
            if key in ALLOWED_FIELDS:
                payload[key] = value
            else:
                dropped.append(key)
        if dropped:
            payload["dropped_fields"] = sorted(dropped)
        if record.exc_info and record.exc_info[0] is not None:
            payload["exc_type"] = record.exc_info[0].__name__
        return json.dumps(payload, default=str)


def configure(component: str, level: int = logging.INFO) -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(SafeJsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    for noisy in ("botocore", "boto3", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    return logging.getLogger(component)
