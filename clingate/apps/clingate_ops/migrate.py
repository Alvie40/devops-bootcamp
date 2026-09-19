"""Apply db/migrations/*.sql in order, once each. Run as the `migrator` role."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

DEFAULT_DIR = Path(__file__).resolve().parents[2] / "db" / "migrations"


def migrate(dsn: str, directory: Path = DEFAULT_DIR) -> list[str]:
    applied: list[str] = []
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version text PRIMARY KEY)")
        done = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
        for path in sorted(directory.glob("*.sql")):
            if path.stem in done:
                continue
            with conn.transaction():
                conn.execute(path.read_text())
                conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
            applied.append(path.stem)
    return applied


if __name__ == "__main__":
    dsn = os.environ.get("CLINGATE_MIGRATOR_DSN")
    if not dsn:
        sys.exit("CLINGATE_MIGRATOR_DSN is required")
    print("applied:", migrate(dsn) or "nothing to do")
