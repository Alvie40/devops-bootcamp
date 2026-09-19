from __future__ import annotations

import pytest

from clingate_lib import hl7
from clingate_lib.ids import raw_key
from clingate_lib.mllp import PeerInfo
from clingate_lib.model import PointerMessage
from clingate_sim.generate import hl7_message
from mllp_listener.app import Listener
from tests.conftest import CERT_A, TENANT_A

PEER = PeerInfo("127.0.0.1:1", CERT_A)


@pytest.fixture
def listener(registry, store, queue, audit):
    return Listener(registry=registry, store=store, queue=queue, audit=audit, processing_id="T")


async def _send(listener, text: str, peer: PeerInfo = PEER) -> hl7.Ack:
    return hl7.parse_ack((await listener.handle(text.encode(), peer)).decode())


async def test_FR3_aa_only_after_durable_write_and_enqueue(listener, store, queue):
    key, text = hl7_message(1, 1)
    ack = await _send(listener, text)
    assert (ack.code, ack.ref_control_id) == ("AA", key)  # MSA-2 echoes MSH-10
    assert raw_key(TENANT_A, "mllp", key) in store.objects
    assert PointerMessage.from_json(queue.sent[0]).idempotency_key == key


async def test_H6_persisted_raw_has_no_direct_identifiers(listener, store):
    key, text = hl7_message(1, 2, with_identifiers=True)
    assert "SINTETICO" in text
    await _send(listener, text)
    stored = store.objects[raw_key(TENANT_A, "mllp", key)].decode()
    assert "SINTETICO" not in stored and "RUA FALSA" not in stored and "19700101" not in stored


async def test_FR4_duplicate_control_id_gets_aa_again(listener, store, queue):
    _, text = hl7_message(1, 3)
    assert (await _send(listener, text)).code == "AA"
    assert (await _send(listener, text)).code == "AA"
    assert len(store.objects) == 1 and len(queue.sent) == 2


async def test_malformed_message_is_ar_with_error_code(listener, store, queue):
    ack = await _send(
        listener, "MSH|^~\\&|LABAPP|LAB1|CLINGATE|CLINGATE|20260901||ORU^R01|X1|T|2.5.1\r"
    )
    assert ack.code == "AR" and ack.error_code in {"101", "102"}
    assert not store.objects and not queue.sent


async def test_garbage_is_ar(listener):
    ack = await _send(listener, "definitely not hl7")
    assert ack.code == "AR"


async def test_unknown_certificate_is_ar(listener, store):
    _, text = hl7_message(1, 4)
    ack = await _send(listener, text, PeerInfo("x", "b" * 64))
    assert ack.code == "AR" and not store.objects


async def test_no_certificate_is_ar_unless_dev_client(listener, registry, store, queue, audit):
    _, text = hl7_message(1, 5)
    assert (await _send(listener, text, PeerInfo("x", None))).code == "AR"
    dev = Listener(registry=registry, store=store, queue=queue, audit=audit,
                   processing_id="T", dev_client_id="lab-a")  # fmt: skip
    assert (await _send(dev, text, PeerInfo("x", None))).code == "AA"


async def test_sender_identity_must_match_certificate_client(listener, store):
    _, text = hl7_message(1, 6, sending_facility="SOMEONE-ELSE")
    ack = await _send(listener, text)
    assert ack.code == "AR" and not store.objects


async def test_wrong_processing_id_is_ar(listener):
    _, text = hl7_message(1, 7, processing_id="P")
    assert (await _send(listener, text)).code == "AR"


async def test_H1_store_failure_is_ae_so_sender_retries(listener, store, queue):
    store.fail_on_put = True
    _, text = hl7_message(1, 8)
    ack = await _send(listener, text)
    assert ack.code == "AE" and not queue.sent


async def test_H1_queue_failure_is_ae(listener, queue):
    queue.fail_on_send = True
    _, text = hl7_message(1, 9)
    assert (await _send(listener, text)).code == "AE"


async def test_audit_events_for_accept_and_reject(listener, audit):
    _, ok = hl7_message(1, 10)
    await _send(listener, ok)
    await _send(listener, "MSH|^~\\&|LABAPP|LAB1|CLINGATE|CLINGATE|20260901||ORU^R01|X2|T|2.5.1\r")
    assert [e.outcome for e in audit.events] == ["accepted", "rejected"]
