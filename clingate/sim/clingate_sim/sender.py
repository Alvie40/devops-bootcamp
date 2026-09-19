"""MLLP load generator: a partner lab dumping a backlog on N connections. Writes a
sent-ledger (JSONL) that the reconciliation step treats as ground truth."""

from __future__ import annotations

import argparse
import asyncio
import json
import time

from clingate_lib import hl7
from clingate_lib.mllp import MllpClient, MllpError

from .generate import hl7_message


async def dump(
    host: str, port: int, *, count: int, connections: int, seed: int, ledger_path: str,
    duplicate_rate: float = 0.01,
) -> dict:  # fmt: skip
    queue: asyncio.Queue[int] = asyncio.Queue()
    for n in range(count):
        queue.put_nowait(n)
    rows: list[dict] = []

    async def worker() -> None:
        client = MllpClient(host, port, timeout=10)
        try:
            while True:
                try:
                    n = queue.get_nowait()
                except asyncio.QueueEmpty:
                    return
                key, text = hl7_message(seed, n)
                for attempt in range(2 if n % int(1 / duplicate_rate or 1e9) == 0 else 1):
                    t0 = time.perf_counter()
                    try:
                        ack = hl7.parse_ack(hl7.decode_bytes(await client.send(text.encode())))
                        status = ack.code
                    except (MllpError, hl7.Hl7Error):
                        status = "ERR"
                    rows.append({"idempotency_key": key, "t_sent": t0, "status": status,
                                 "latency_ms": (time.perf_counter() - t0) * 1000, "dup": attempt > 0})  # fmt: skip
        finally:
            await client.close()

    t0 = time.perf_counter()
    await asyncio.gather(*(worker() for _ in range(connections)))
    elapsed = time.perf_counter() - t0
    with open(ledger_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    lat = sorted(r["latency_ms"] for r in rows)
    return {
        "sent": len(rows),
        "elapsed_s": round(elapsed, 2),
        "msg_per_s": round(len(rows) / elapsed, 1) if elapsed else 0,
        "p50_ms": round(lat[len(lat) // 2], 2) if lat else None,
        "p99_ms": round(lat[int(len(lat) * 0.99) - 1], 2) if lat else None,
        "non_aa": sum(1 for r in rows if r["status"] != "AA"),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=2575)
    ap.add_argument("--count", type=int, default=1000)
    ap.add_argument("--connections", type=int, default=1)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--ledger", default="loadtest/out/ledger.jsonl")
    a = ap.parse_args()
    print(json.dumps(asyncio.run(dump(a.host, a.port, count=a.count, connections=a.connections,
                                      seed=a.seed, ledger_path=a.ledger)), indent=2))  # fmt: skip
