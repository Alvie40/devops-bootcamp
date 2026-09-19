"""Post-run reconciliation (docs/LOADTEST.md section 8). Any violation fails the run,
regardless of latency: a fast run that loses or duplicates a record is a failed run."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from clingate_lib.ids import raw_key
from clingate_lib.ports import RawStore
from clingate_lib.repo import Repository

ACKED = {"202", "AA"}


@dataclass
class Report:
    checks: dict[str, bool] = field(default_factory=dict)
    details: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return all(self.checks.values())

    def add(self, name: str, ok: bool, detail: str) -> None:
        self.checks[name], self.details[name] = ok, detail


def load_ledger(path: str | Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def reconcile(
    ledger: Iterable[dict],
    *,
    tenant_id: str,
    source: str,
    store: RawStore,
    repo: Repository,
    expected_observations: int | None = None,
) -> Report:
    rows = [r for r in ledger if str(r.get("status")) in ACKED]
    unique = sorted({r["idempotency_key"] for r in rows})
    report = Report()

    missing = [k for k in unique if not store.exists(raw_key(tenant_id, source, k))]
    report.add(
        "I1 acked => raw object exists", not missing, f"{len(missing)} missing of {len(unique)}"
    )

    events = repo.count_events(tenant_id, source, unique)
    report.add(
        "I2 one ingest_event per unique key",
        events == len(unique),
        f"{events} events, {len(unique)} unique keys",
    )

    if expected_observations is not None:
        got = repo.count_observations(tenant_id)
        report.add(
            "I3 observation count",
            got == expected_observations,
            f"{got} vs {expected_observations}",
        )

    pending = repo.unfinished_exports(tenant_id)
    report.add("I4 no export left pending", pending == 0, f"{pending} pending")
    return report


def _main() -> int:
    import argparse

    from clingate_lib.config import Settings
    from clingate_lib.wiring import build_repo, build_store

    ap = argparse.ArgumentParser(description="Reconcile a sent-ledger against S3 and the database")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--tenant", required=True)
    ap.add_argument("--source", choices=("http", "mllp"), required=True)
    ap.add_argument("--expected-observations", type=int)
    a = ap.parse_args()
    s = Settings.from_env()
    report = reconcile(
        load_ledger(a.ledger),
        tenant_id=a.tenant,
        source=a.source,
        store=build_store(s),
        repo=build_repo(s),
        expected_observations=a.expected_observations,
    )
    for name, ok in report.checks.items():
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {report.details[name]}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(_main())
