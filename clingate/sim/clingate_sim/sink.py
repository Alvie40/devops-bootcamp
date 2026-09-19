"""Downstream interface-engine simulator with knobs: latency, AE rate, AR rate."""

from __future__ import annotations

import argparse
import asyncio
import random
import uuid

from clingate_lib import hl7
from clingate_lib.mllp import PeerInfo, serve


class Sink:
    def __init__(
        self, *, latency_ms: float = 0, ae_rate: float = 0.0, ar_rate: float = 0.0, seed: int = 1
    ):
        self.latency_ms, self.ae_rate, self.ar_rate = latency_ms, ae_rate, ar_rate
        self._rng = random.Random(seed)
        self.received: list[str] = []
        self.control_ids: list[str] = []

    async def handle(self, frame: bytes, peer: PeerInfo) -> bytes:
        if self.latency_ms:
            await asyncio.sleep(self.latency_ms / 1000)
        try:
            text = hl7.decode_bytes(frame)
        except hl7.Hl7Error:
            text = ""
        msh = hl7.parse_msh_lenient(text)
        self.received.append(text)
        if msh:
            self.control_ids.append(msh.control_id)
        roll = self._rng.random()
        code, err = "AA", None
        if roll < self.ar_rate:
            code, err = "AR", "rejected by simulator"
        elif roll < self.ar_rate + self.ae_rate:
            code, err = "AE", "simulated transient error"
        return hl7.build_ack(
            msh, code, control_id="SINK" + uuid.uuid4().hex[:12], text=err
        ).encode()


async def _main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=2576)
    ap.add_argument("--latency-ms", type=float, default=0)
    ap.add_argument("--ae-rate", type=float, default=0.0)
    ap.add_argument("--ar-rate", type=float, default=0.0)
    a = ap.parse_args()
    sink = Sink(latency_ms=a.latency_ms, ae_rate=a.ae_rate, ar_rate=a.ar_rate)
    server = await serve(sink.handle, "127.0.0.1", a.port)
    print(f"sink listening on :{a.port} latency={a.latency_ms}ms ae={a.ae_rate} ar={a.ar_rate}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(_main())
