from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sim"))

from clingate_lib.audit import MemoryAuditSink  # noqa: E402
from clingate_lib.clients import StaticClientRegistry  # noqa: E402
from clingate_lib.memory import MemoryQueue, MemoryRawStore  # noqa: E402
from clingate_lib.model import Client  # noqa: E402
from clingate_lib.repo import Destination  # noqa: E402
from clingate_sim.devauth import ISSUER, DevKeys  # noqa: E402

TENANT_A = "11111111-1111-1111-1111-111111111111"
TENANT_B = "22222222-2222-2222-2222-222222222222"
CERT_A = "a" * 64


@pytest.fixture(scope="session")
def keys() -> DevKeys:
    return DevKeys.generate()


@pytest.fixture
def issuer() -> str:
    return ISSUER


@pytest.fixture
def registry() -> StaticClientRegistry:
    return StaticClientRegistry(
        [
            Client("dev-device-client", TENANT_A, "http"),
            Client("dev-device-b", TENANT_B, "http"),
            Client("disabled-client", TENANT_A, "http", enabled=False),
            Client(
                "lab-a",
                TENANT_A,
                "mllp",
                cert_sha256=CERT_A,
                sending_application="LABAPP",
                sending_facility="LAB1",
            ),  # fmt: skip
        ]
    )


@pytest.fixture
def store() -> MemoryRawStore:
    return MemoryRawStore()


@pytest.fixture
def queue() -> MemoryQueue:
    return MemoryQueue()


@pytest.fixture
def audit() -> MemoryAuditSink:
    return MemoryAuditSink()


def make_destination(port: int = 1, dest_id: str = "33333333-3333-3333-3333-333333333333"):
    return Destination(
        id=dest_id, host="127.0.0.1", port=port, max_connections=2,
        sending_app="CLINGATE", sending_facility="CLINGATE",
        receiving_app="SPONSOR", receiving_facility="SPONSORHQ",
    )  # fmt: skip


def dump_json(obj) -> str:
    return json.dumps(obj)
