from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    backend: str  # "memory" | "aws" | "null" (baseline only)
    raw_bucket: str
    ingest_queue_url: str
    export_queue_url: str
    db_dsn: str | None
    clients_file: str
    processing_id: str

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            backend=_env("CLINGATE_BACKEND", "memory") or "memory",
            raw_bucket=_env("CLINGATE_RAW_BUCKET", "clingate-raw-dev") or "",
            ingest_queue_url=_env("CLINGATE_INGEST_QUEUE_URL", "") or "",
            export_queue_url=_env("CLINGATE_EXPORT_QUEUE_URL", "") or "",
            db_dsn=_env("CLINGATE_DB_DSN"),
            clients_file=_env("CLINGATE_CLIENTS_FILE", "dev/clients.json") or "",
            processing_id=_env("CLINGATE_PROCESSING_ID", "T") or "T",
        )
