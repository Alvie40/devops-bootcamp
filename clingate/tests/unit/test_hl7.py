from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from clingate_lib import hl7
from clingate_lib.model import Observation
from clingate_sim.generate import hl7_message

TS = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


def _obs(**kw) -> Observation:
    base = dict(seq=1, code_system="LOINC", code="8867-4", code_text="Heart rate",
                value_num=Decimal("72"), unit="/min", observed_at=TS)  # fmt: skip
    return Observation(**{**base, **kw})


def _build(observations, pseudonym="subj-1", control_id="C1"):
    return hl7.build_oru(
        control_id=control_id, sending_app="A", sending_facility="F", receiving_app="R",
        receiving_facility="RF", processing_id="T", pseudonym=pseudonym,
        observations=observations, timestamp=TS,
    )  # fmt: skip


def test_build_parse_roundtrip():
    parsed = hl7.parse_oru(
        _build([_obs(), _obs(seq=2, code="59408-5", value_num=Decimal("97.5"), unit="%")])
    )
    assert parsed.msh.control_id == "C1"
    assert parsed.pseudonym == "subj-1"
    assert [o.code for o in parsed.observations] == ["8867-4", "59408-5"]
    assert parsed.observations[1].value_num == Decimal("97.5")
    assert parsed.observations[0].code_system == "LOINC"
    assert parsed.observations[0].observed_at == TS


def test_FR6_missing_obx_rejected():
    text = _build([_obs()]).replace("OBX", "ZZZ")
    with pytest.raises(hl7.Hl7Error) as e:
        hl7.parse_oru(text)
    assert e.value.code == "101"


def test_numeric_without_unit_rejected():
    with pytest.raises(hl7.Hl7Error) as e:
        hl7.parse_oru(_build([_obs(unit=None)]))
    assert e.value.code == "101"


def test_non_numeric_value_rejected():
    text = _build([_obs()]).replace("|72|", "|abc|")
    with pytest.raises(hl7.Hl7Error) as e:
        hl7.parse_oru(text)
    assert e.value.code == "102"


@pytest.mark.parametrize("bad", ["ADT^A01", "ORM^O01"])
def test_wrong_message_type(bad):
    with pytest.raises(hl7.Hl7Error):
        hl7.parse_oru(_build([_obs()]).replace("ORU^R01^ORU_R01", bad))


def test_limits():
    with pytest.raises(hl7.Hl7Error):
        hl7.decode_bytes(b"MSH|" + b"x" * (hl7.MAX_MESSAGE_BYTES + 1))
    many = "MSH|^~\\&|A|F|R|RF|20260901||ORU^R01|1|T|2.5.1\r" + "OBX|1\r" * (hl7.MAX_SEGMENTS + 1)
    with pytest.raises(hl7.Hl7Error):
        hl7.parse_message(many)


def test_latin1_charset_honoured():
    text = _build([_obs(value_num=None, value_text="coração", unit=None)]).replace(
        "UNICODE UTF-8", "8859/1"
    )
    parsed = hl7.parse_oru(hl7.decode_bytes(text.encode("latin-1")))
    assert parsed.observations[0].value_text == "coração"


def test_unsupported_charset_rejected():
    text = _build([_obs()]).replace("UNICODE UTF-8", "EBCDIC")
    with pytest.raises(hl7.Hl7Error):
        hl7.decode_bytes(text.encode())


def test_dtm_forms():
    assert hl7.parse_dtm("2026").year == 2026
    assert hl7.parse_dtm("20260901120000-0300").utcoffset().total_seconds() == -3 * 3600
    with pytest.raises(hl7.Hl7Error):
        hl7.parse_dtm("20261301")


def test_ack_roundtrip_and_no_content_echo():
    _, text = hl7_message(1, 1)
    msh = hl7.parse_msh_lenient(text)
    ack = hl7.parse_ack(
        hl7.build_ack(msh, "AR", control_id="X1", text="PID-3 missing", error_code="101")
    )
    assert (ack.code, ack.ref_control_id, ack.error_code) == ("AR", "S1-M00000001", "101")


def test_ack_for_unparseable_message():
    ack = hl7.parse_ack(hl7.build_ack(None, "AR", control_id="X", text="bad", error_code="100"))
    assert ack.code == "AR"


def test_H6_scrub_drops_direct_identifiers():
    _, text = hl7_message(1, 1, with_identifiers=True)
    assert "SINTETICO" in text and "RUA FALSA" in text
    scrubbed, dropped = hl7.scrub_identifiers(text)
    assert "SINTETICO" not in scrubbed and "RUA FALSA" not in scrubbed
    assert "19700101" not in scrubbed
    assert dropped >= 3
    assert hl7.parse_oru(scrubbed).pseudonym == hl7.parse_oru(text).pseudonym
    assert hl7.parse_oru(scrubbed).observations == hl7.parse_oru(text).observations


def test_scrub_drops_next_of_kin_segment():
    _, text = hl7_message(1, 2)
    text += "NK1|1|FAKE^NAME\r"
    scrubbed, _ = hl7.scrub_identifiers(text)
    assert "NK1" not in scrubbed and "FAKE" not in scrubbed


def test_scrub_normalises_charset_to_utf8():
    _, text = hl7_message(1, 3)
    assert "UNICODE UTF-8" in hl7.scrub_identifiers(text.replace("UNICODE UTF-8", "8859/1"))[0]


@settings(max_examples=300, deadline=None)
@given(st.text(max_size=2000))
def test_H8_parser_only_raises_hl7error(text):
    for fn in (hl7.parse_message, hl7.parse_oru, hl7.scrub_identifiers, hl7.parse_ack):
        with contextlib.suppress(hl7.Hl7Error):
            fn(text)


@settings(max_examples=200, deadline=None)
@given(st.binary(max_size=2000))
def test_H8_decode_only_raises_hl7error(raw):
    with contextlib.suppress(hl7.Hl7Error):
        hl7.decode_bytes(raw)


_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc"), blacklist_characters="\x00"),
    max_size=40,
)


@settings(max_examples=200, deadline=None)
@given(value=_text)
def test_H7_text_value_roundtrip_with_delimiters(value):
    """Values containing | ^ ~ \\ & and newlines must survive build -> parse."""
    tricky = value + "|^~\\&"
    parsed = hl7.parse_oru(_build([_obs(value_num=None, value_text=tricky, unit=None)]))
    assert parsed.observations[0].value_text == tricky


@settings(max_examples=100, deadline=None)
@given(
    st.decimals(
        allow_nan=False, allow_infinity=False, min_value=-(10**9), max_value=10**9, places=4
    )
)
def test_numeric_roundtrip(d):
    parsed = hl7.parse_oru(_build([_obs(value_num=d)]))
    assert parsed.observations[0].value_num == d
