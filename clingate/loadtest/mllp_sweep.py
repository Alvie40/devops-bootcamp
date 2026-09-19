"""Hypothesis 2 (MLLP is serial per connection), measured locally.

Part A: sink with a fixed ACK latency; throughput should track connections / latency.
Part B: our listener with the null backend and zero network latency; shows where the listener's
own CPU (parse + scrub) becomes the limit, once the protocol wait is out of the picture."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import time

from clingate_sim.sender import dump

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "loadtest", "out", "mllp-sweep.jsonl")


async def _wait_port(port: int) -> None:
    for _ in range(60):
        try:
            _, w = await asyncio.open_connection("127.0.0.1", port)
            w.close()
            return
        except OSError:
            await asyncio.sleep(0.25)
    raise RuntimeError(f"port {port} never opened")


async def sweep(port: int, conns: list[int], per_conn: int, predict_ms: float | None) -> None:
    print(f"{'conns':<6} {'msg/s':<9} {'p50_ms':<8} {'p99_ms':<8} {'non_aa':<7} predicted")
    for c in conns:
        r = await dump("127.0.0.1", port, count=per_conn * c, connections=c, seed=c,
                       ledger_path=LEDGER, duplicate_rate=0)  # fmt: skip
        pred = f"{c * 1000 / predict_ms:.0f}" if predict_ms else "-"
        print(
            f"{c:<6} {r['msg_per_s']:<9} {r['p50_ms']:<8} {r['p99_ms']:<8} {r['non_aa']:<7} {pred}"
        )


async def main() -> None:
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    latency = float(os.environ.get("ACK_LATENCY_MS", "20"))
    print(f"== A. sink, ACK latency {latency} ms: throughput should be ~ connections / latency")
    sink_cmd = [
        sys.executable,
        "-m",
        "clingate_sim.sink",
        "--port",
        "2577",
        "--latency-ms",
        str(latency),
    ]
    sink = subprocess.Popen(sink_cmd, stdout=subprocess.DEVNULL)  # noqa: S603
    try:
        await _wait_port(2577)
        await sweep(2577, [1, 2, 4, 8, 16, 32], 60, latency + 1)  # +~1 ms of real work per ACK
    finally:
        sink.terminate()

    print("\n== B. listener (null backend), no network latency: the listener's own ceiling")
    env = {**os.environ, "CLINGATE_BACKEND": "null", "CLINGATE_DEV_CLIENT": "dev-lab-client",
           "CLINGATE_CLIENTS_FILE": os.path.join(ROOT, "dev", "clients.json"), "PORT": "2578"}  # fmt: skip
    lst = subprocess.Popen(  # noqa: S603
        [sys.executable, "-m", "mllp_listener"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        await _wait_port(2578)
        t0 = time.time()
        await sweep(2578, [1, 4, 16, 64], 400, None)
        print(f"(part B took {time.time() - t0:.1f}s)")
    finally:
        lst.terminate()


if __name__ == "__main__":
    asyncio.run(main())
