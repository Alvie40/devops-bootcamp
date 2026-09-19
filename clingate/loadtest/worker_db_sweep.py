"""Hypothesis 1 (worker -> Postgres is the bottleneck), measured locally.

One worker *process*, k threads, pool of k connections, against Postgres in Docker (not Aurora).
Each ingest is one transaction: event + subject/device upserts + N observations + export intent.
Shows how throughput and per-call latency move with concurrency, and where the pool/DB stops helping.
Python parsing holds the GIL, so a single process cannot use more than ~1 core for parsing:
horizontal scale is more worker processes, which is what KEDA does; the DB is what they share."""

from __future__ import annotations

import hashlib
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from clingate_lib.ids import ingest_id, raw_key
from clingate_lib.memory import MemoryQueue, MemoryRawStore
from clingate_lib.model import PointerMessage
from clingate_lib.repo_pg import PgRepository
from clingate_ops.devdb import reset_and_seed
from clingate_sim.generate import device_batch, hl7_message
from clingate_worker.core import process_ingest

TENANT = "11111111-1111-1111-1111-111111111111"
MIGRATOR = "postgresql://migrator:dev-migrator@127.0.0.1:55432/clingate"
APP = "postgresql://app_rw:dev-app@127.0.0.1:55432/clingate"


def make_pointers(store: MemoryRawStore, source: str, seed: int, n: int, n_obs: int) -> list[str]:
    out = []
    for i in range(n):
        if source == "mllp":
            key, text = hl7_message(seed, i, n_obs=n_obs, with_identifiers=False)
            data = text.encode()
        else:
            key, data = device_batch(seed, i, n_obs=n_obs)
        k = raw_key(TENANT, source, key)
        sha = hashlib.sha256(data).hexdigest()
        store.put_if_absent(k, data, sha)
        out.append(PointerMessage(ingest_id(TENANT, source, key), TENANT, "c", source, key, k, sha,
                                  datetime.now(UTC).isoformat(), "t").to_json())  # fmt: skip
    return out


def run(threads: int, source: str, n: int, n_obs: int, seed: int) -> None:
    store, export_q = MemoryRawStore(), MemoryQueue()
    pointers = make_pointers(store, source, seed, n, n_obs)
    repo = PgRepository(APP, min_size=threads, max_size=threads)
    lat: list[float] = []

    def one(body: str) -> None:
        t = time.perf_counter()
        process_ingest(body, store=store, repo=repo, export_queue=export_q)
        lat.append((time.perf_counter() - t) * 1000)

    t0 = time.perf_counter()
    with ThreadPoolExecutor(threads) as ex:
        list(ex.map(one, pointers))
    el = time.perf_counter() - t0
    repo.close()
    lat.sort()
    print(
        f"{threads:<8} {n / el:<11.0f} {n * n_obs / el:<10.0f} {statistics.median(lat):<8.1f} {lat[int(len(lat) * 0.99) - 1]:<8.1f}"
    )


if __name__ == "__main__":
    reset_and_seed(MIGRATOR)
    n = int(os.environ.get("N", "1500"))
    for source, n_obs in (("mllp", 12), ("http", 30)):
        print(f"\n== source={source}, {n_obs} observations/message, N={n}")
        print(f"{'threads':<8} {'ingest/s':<11} {'obs/s':<10} {'p50_ms':<8} {'p99_ms':<8}")
        for i, k in enumerate([1, 2, 4, 8, 16]):
            run(k, source, n, n_obs, seed=1000 * (1 if source == "mllp" else 2) + i)
    sys.exit(0)
