"""MLLP framing plus a small asyncio server and client.

MLLP is strictly request/response per connection: one outstanding message, then wait
for the ACK. Per-connection throughput is therefore ~1 / ACK latency; scale with more
connections (see docs/LOADTEST.md, hypothesis 2).
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import ssl
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

VT = b"\x0b"
END = b"\x1c\x0d"
DEFAULT_MAX_FRAME = 1024 * 1024


class MllpError(Exception):
    pass


class MllpFramingError(MllpError):
    pass


def frame(payload: bytes) -> bytes:
    return VT + payload + END


class FrameDecoder:
    def __init__(self, max_frame: int = DEFAULT_MAX_FRAME) -> None:
        self.max_frame = max_frame
        self._buf = bytearray()
        self._in_frame = False

    def feed(self, data: bytes) -> list[bytes]:
        self._buf += data
        out: list[bytes] = []
        while True:
            if not self._in_frame:
                stripped = self._buf.lstrip(b"\r\n")
                if len(stripped) != len(self._buf):
                    del self._buf[: len(self._buf) - len(stripped)]
                if not self._buf:
                    break
                if self._buf[0:1] != VT:
                    raise MllpFramingError("data before start block")
                del self._buf[:1]
                self._in_frame = True
            end = self._buf.find(END)
            if end == -1:
                if len(self._buf) > self.max_frame:
                    raise MllpFramingError("frame too large")
                break
            if end > self.max_frame:
                raise MllpFramingError("frame too large")
            out.append(bytes(self._buf[:end]))
            del self._buf[: end + 2]
            self._in_frame = False
        return out


@dataclass(frozen=True)
class PeerInfo:
    addr: str
    cert_sha256: str | None


Handler = Callable[[bytes, PeerInfo], Awaitable[bytes | None]]


async def serve(
    handler: Handler,
    host: str,
    port: int,
    *,
    ssl_context: ssl.SSLContext | None = None,
    max_frame: int = DEFAULT_MAX_FRAME,
    idle_timeout: float = 60.0,
    max_connections: int | None = None,
) -> asyncio.Server:
    active = 0

    async def on_connect(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        nonlocal active
        if max_connections is not None and active >= max_connections:
            writer.close()
            return
        active += 1
        try:
            peername = writer.get_extra_info("peername")
            addr = f"{peername[0]}:{peername[1]}" if peername else "unknown"
            cert_hash = None
            ssl_obj = writer.get_extra_info("ssl_object")
            if ssl_obj is not None:
                der = ssl_obj.getpeercert(binary_form=True)
                if der:
                    cert_hash = hashlib.sha256(der).hexdigest()
            peer = PeerInfo(addr=addr, cert_sha256=cert_hash)
            decoder = FrameDecoder(max_frame)
            while True:
                data = await asyncio.wait_for(reader.read(65536), timeout=idle_timeout)
                if not data:
                    break
                for msg in decoder.feed(data):
                    response = await handler(msg, peer)
                    if response is not None:
                        writer.write(frame(response))
                        await writer.drain()
        except (MllpFramingError, TimeoutError, ConnectionError, ssl.SSLError):
            pass
        finally:
            active -= 1
            writer.close()

    return await asyncio.start_server(on_connect, host, port, ssl=ssl_context)


class MllpClient:
    def __init__(
        self,
        host: str,
        port: int,
        *,
        ssl_context: ssl.SSLContext | None = None,
        timeout: float = 10.0,
        max_frame: int = DEFAULT_MAX_FRAME,
    ) -> None:
        self.host, self.port = host, port
        self._ssl = ssl_context
        self._timeout = timeout
        self._decoder = FrameDecoder(max_frame)
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port, ssl=self._ssl), self._timeout
            )
        except (TimeoutError, OSError) as e:
            raise MllpError("connect failed") from e

    async def send(self, payload: bytes) -> bytes:
        if self._writer is None or self._reader is None:
            await self.connect()
        assert self._writer is not None and self._reader is not None  # noqa: S101
        try:
            self._writer.write(frame(payload))
            await asyncio.wait_for(self._writer.drain(), self._timeout)
            while True:
                data = await asyncio.wait_for(self._reader.read(65536), self._timeout)
                if not data:
                    raise MllpError("connection closed before ACK")
                frames = self._decoder.feed(data)
                if frames:
                    return frames[0]
        except (TimeoutError, OSError, MllpError) as e:
            await self.close()
            raise MllpError("send failed") from e

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            with contextlib.suppress(OSError, ssl.SSLError):
                await self._writer.wait_closed()
        self._reader = self._writer = None
        self._decoder = FrameDecoder(self._decoder.max_frame)
