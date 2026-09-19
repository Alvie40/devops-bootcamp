"""Dev only: wipe the `clingate` database, migrate, seed. Never point this at anything shared."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

from .migrate import migrate

SEED = Path(__file__).resolve().parents[2] / "dev" / "seed.sql"


def reset_and_seed(dsn: str) -> None:
    with psycopg.connect(dsn, autocommit=True) as c:
        c.execute("DROP SCHEMA public CASCADE")
        c.execute("CREATE SCHEMA public")
        c.execute("GRANT USAGE ON SCHEMA public TO app_rw, auditor_ro")
    migrate(dsn)
    with psycopg.connect(dsn, autocommit=True) as c:
        c.execute(SEED.read_text())


if __name__ == "__main__":
    dsn = os.environ.get("CLINGATE_MIGRATOR_DSN")
    if not dsn:
        sys.exit("CLINGATE_MIGRATOR_DSN is required")
    reset_and_seed(dsn)
    print("dev database reset and seeded")
