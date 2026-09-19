from __future__ import annotations

import asyncio

import pytest

from clingate_lib.mllp import FrameDecoder, MllpClient, MllpError, MllpFramingError, frame, serve


def test_frame_roundtrip_and_fragmentation():
    d = FrameDecoder()
    wire = frame(b"HELLO") + frame(b"WORLD")
    got = []
    for i in range(len(wire)):  # one byte at a time
        got += d.feed(wire[i : i + 1])
    assert got == [b"HELLO", b"WORLD"]


def test_tolerates_crlf_between_frames():
    assert FrameDecoder().feed(frame(b"A") + b"\r\n" + frame(b"B")) == [b"A", b"B"]


def test_garbage_before_start_block():
    with pytest.raises(MllpFramingError):
        FrameDecoder().feed(b"garbage")


def test_oversize_frame():
    d = FrameDecoder(max_frame=10)
    with pytest.raises(MllpFramingError):
        d.feed(b"\x0b" + b"x" * 50)


async def test_client_server_roundtrip():
    async def echo_upper(msg: bytes, peer) -> bytes:
        return msg.upper()

    server = await serve(echo_upper, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    async with server:
        c = MllpClient("127.0.0.1", port)
        assert await c.send(b"abc") == b"ABC"
        assert await c.send(b"def") == b"DEF"  # connection reuse
        await c.close()


async def test_idle_timeout_closes_connection():
    async def h(msg, peer):
        return msg

    server = await serve(h, "127.0.0.1", 0, idle_timeout=0.1)
    port = server.sockets[0].getsockname()[1]
    async with server:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        assert await asyncio.wait_for(reader.read(1), 2) == b""
        writer.close()


async def test_client_connect_failure_is_mllp_error():
    with pytest.raises(MllpError):
        await MllpClient("127.0.0.1", 1, timeout=0.5).send(b"x")
