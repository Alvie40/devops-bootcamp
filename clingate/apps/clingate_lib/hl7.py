"""Strict, minimal HL7 v2.5.1 ORU^R01 parser/builder.

Untrusted input on an unauthenticated protocol: every limit is enforced before
allocation-heavy work, the parser only raises Hl7Error, and error texts never echo
message content (they can end up in ACKs and logs).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from .model import Observation

MAX_MESSAGE_BYTES = 1024 * 1024
MAX_SEGMENTS = 5000
MAX_FIELD_CHARS = 65536
_MAX_STRING_VALUE = 2000
_PSEUDONYM = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_DTM = re.compile(r"^(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?(?:\.(\d{1,4}))?([+-]\d{4})?$")
_SEGMENT_NAME = re.compile(r"^[A-Z][A-Z0-9]{2}$")
_SYSTEM_TO_HL7 = {"LOINC": "LN"}
_SYSTEM_FROM_HL7 = {v: k for k, v in _SYSTEM_TO_HL7.items()}
_DROP_SEGMENTS = frozenset({"NK1", "GT1", "IN1", "IN2", "IN3"})
_PID_KEEP = frozenset({1, 3})


class Hl7Error(ValueError):
    """`code` is an HL70357 error code; `text` is safe to send to the peer."""

    def __init__(self, code: str, text: str) -> None:
        super().__init__(f"{code}: {text}")
        self.code = code
        self.text = text


@dataclass(frozen=True)
class Separators:
    field: str = "|"
    comp: str = "^"
    rep: str = "~"
    esc: str = "\\"
    sub: str = "&"


@dataclass(frozen=True)
class Segment:
    name: str
    fields: tuple[str, ...]  # fields[i] is HL7 field i+1 (MSH-1 is the separator itself)

    def get(self, n: int) -> str:
        return self.fields[n - 1] if 0 < n <= len(self.fields) else ""


@dataclass(frozen=True)
class Message:
    seps: Separators
    segments: tuple[Segment, ...]

    def all(self, name: str) -> list[Segment]:
        return [s for s in self.segments if s.name == name]

    def first(self, name: str) -> Segment | None:
        return next((s for s in self.segments if s.name == name), None)


@dataclass(frozen=True)
class Msh:
    sending_app: str
    sending_facility: str
    receiving_app: str
    receiving_facility: str
    timestamp: str
    message_type: str
    control_id: str
    processing_id: str
    version: str
    charset: str


@dataclass(frozen=True)
class ParsedOru:
    msh: Msh
    pseudonym: str
    observations: tuple[Observation, ...]


@dataclass(frozen=True)
class Ack:
    code: str
    ref_control_id: str
    error_code: str | None
    error_text: str | None


def _split_segments(text: str) -> list[str]:
    return [line for line in re.split(r"\r\n|\r|\n", text) if line]


def _comp(seps: Separators, value: str, i: int) -> str:
    first_rep = value.split(seps.rep)[0]
    parts = first_rep.split(seps.comp)
    return unescape(seps, parts[i - 1]) if i <= len(parts) else ""


def unescape(seps: Separators, s: str) -> str:
    if seps.esc not in s:
        return s
    table = {
        "F": seps.field,
        "S": seps.comp,
        "T": seps.sub,
        "R": seps.rep,
        "E": seps.esc,
        ".br": "\n",
    }
    pattern = re.compile(
        re.escape(seps.esc) + r"([^" + re.escape(seps.esc) + r"]*)" + re.escape(seps.esc)
    )
    return pattern.sub(lambda m: table.get(m.group(1), m.group(0)), s)


def escape(seps: Separators, s: str) -> str:
    s = s.replace(seps.esc, seps.esc + "E" + seps.esc)
    s = s.replace(seps.field, seps.esc + "F" + seps.esc)
    s = s.replace(seps.comp, seps.esc + "S" + seps.esc)
    s = s.replace(seps.sub, seps.esc + "T" + seps.esc)
    s = s.replace(seps.rep, seps.esc + "R" + seps.esc)
    return s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", seps.esc + ".br" + seps.esc)


def decode_bytes(raw: bytes) -> str:
    """Bytes -> text, honouring MSH-18. UTF-8 and ISO-8859-1 only (Latin-1 is common
    in Brazilian lab systems). Absent MSH-18: strict UTF-8, falling back to Latin-1."""
    if len(raw) > MAX_MESSAGE_BYTES:
        raise Hl7Error("100", "message too large")
    head = raw[:4096].decode("latin-1")
    if not head.startswith("MSH") or len(head) < 4:
        raise Hl7Error("100", "message does not start with MSH")
    first_line = re.split(r"\r|\n", head, maxsplit=1)[0]
    parts = first_line.split(head[3])
    charset = parts[17].strip().upper() if len(parts) > 17 else ""
    if charset in ("8859/1", "ISO-8859-1", "ISO_8859-1", "LATIN1"):
        return raw.decode("latin-1")
    if charset in ("UNICODE UTF-8", "UTF-8", "UTF8", "UNICODE"):
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as e:
            raise Hl7Error("102", "invalid UTF-8") from e
    if charset in ("", "ASCII"):
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin-1")
    raise Hl7Error("102", "unsupported character set")


def parse_message(text: str) -> Message:
    lines = _split_segments(text)
    if not lines:
        raise Hl7Error("100", "empty message")
    if len(lines) > MAX_SEGMENTS:
        raise Hl7Error("100", "too many segments")
    head = lines[0]
    if not head.startswith("MSH") or len(head) < 8:
        raise Hl7Error("100", "message does not start with MSH")
    fs = head[3]
    enc = head[4:].split(fs, 1)[0]
    if len(enc) < 4:
        raise Hl7Error("100", "invalid encoding characters")
    seps = Separators(field=fs, comp=enc[0], rep=enc[1], esc=enc[2], sub=enc[3])
    segments: list[Segment] = []
    for line in lines:
        name = line[:3]
        if not _SEGMENT_NAME.match(name):
            raise Hl7Error("100", "invalid segment name")
        parts = line.split(fs)
        if any(len(p) > MAX_FIELD_CHARS for p in parts):
            raise Hl7Error("100", "field too long")
        fields = (fs, *parts[1:]) if name == "MSH" else tuple(parts[1:])
        segments.append(Segment(name, fields))
    if segments[0].name != "MSH":
        raise Hl7Error("100", "first segment must be MSH")
    return Message(seps, tuple(segments))


def _msh(msg: Message) -> Msh:
    h = msg.segments[0]
    s = msg.seps
    return Msh(
        sending_app=_comp(s, h.get(3), 1),
        sending_facility=_comp(s, h.get(4), 1),
        receiving_app=_comp(s, h.get(5), 1),
        receiving_facility=_comp(s, h.get(6), 1),
        timestamp=_comp(s, h.get(7), 1),
        message_type=h.get(9),
        control_id=unescape(s, h.get(10)),
        processing_id=_comp(s, h.get(11), 1),
        version=_comp(s, h.get(12), 1),
        charset=h.get(18),
    )


def parse_msh_lenient(text: str) -> Msh | None:
    """Best-effort MSH for building a NACK. Never raises."""
    try:
        return _msh(parse_message(text))
    except Hl7Error:
        return None


def parse_dtm(value: str) -> datetime:
    m = _DTM.match(value.strip())
    if not m:
        raise Hl7Error("102", "invalid timestamp")
    y, mo, d, h, mi, s, frac, tz = m.groups()
    tzinfo = UTC
    if tz:
        offset = timedelta(hours=int(tz[1:3]), minutes=int(tz[3:5]))
        tzinfo = timezone(offset if tz[0] == "+" else -offset)
    try:
        return datetime(
            int(y),
            int(mo or 1),
            int(d or 1),
            int(h or 0),
            int(mi or 0),
            int(s or 0),
            int((frac or "0").ljust(6, "0")[:6]),
            tzinfo=tzinfo,
        )
    except ValueError as e:
        raise Hl7Error("102", "invalid timestamp") from e


def _format_dtm(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y%m%d%H%M%S+0000")


def parse_oru(text: str) -> ParsedOru:
    msg = parse_message(text)
    s = msg.seps
    msh = _msh(msg)
    mt = msg.segments[0].get(9).split(s.comp)
    if mt[0] != "ORU":
        raise Hl7Error("200", "unsupported message type")
    if len(mt) < 2 or mt[1] != "R01":
        raise Hl7Error("201", "unsupported event")
    if not msh.version.startswith("2."):
        raise Hl7Error("203", "unsupported version")
    if not msh.control_id or len(msh.control_id) > 199:
        raise Hl7Error("101", "MSH-10 missing or too long")

    pid = msg.first("PID")
    if pid is None:
        raise Hl7Error("101", "PID segment missing")
    pseudonym = _comp(s, pid.get(3), 1)
    if not pseudonym:
        raise Hl7Error("101", "PID-3 missing")
    if not _PSEUDONYM.match(pseudonym):
        raise Hl7Error("102", "PID-3 format invalid")

    obr = msg.first("OBR")
    fallback_time: datetime | None = None
    for candidate in (obr.get(7) if obr else "", msg.segments[0].get(7)):
        if candidate:
            fallback_time = parse_dtm(_comp(s, candidate, 1))
            break

    observations: list[Observation] = []
    for i, obx in enumerate(msg.all("OBX"), start=1):
        vtype = obx.get(2)
        if vtype not in ("NM", "ST", "SN"):
            raise Hl7Error("103", "unsupported OBX value type")
        code = _comp(s, obx.get(3), 1)
        system_raw = _comp(s, obx.get(3), 3)
        if not code or not system_raw:
            raise Hl7Error("101", "OBX-3 code or coding system missing")
        raw_value = unescape(s, obx.get(5).split(s.rep)[0])
        unit = _comp(s, obx.get(6), 1) or None
        value_num: Decimal | None = None
        value_text: str | None = None
        if vtype == "NM":
            if unit is None:
                raise Hl7Error("101", "OBX-6 unit required for numeric value")
            try:
                value_num = Decimal(raw_value)
            except InvalidOperation as e:
                raise Hl7Error("102", "OBX-5 not numeric") from e
            if not value_num.is_finite():
                raise Hl7Error("102", "OBX-5 not finite")
        else:
            if len(raw_value) > _MAX_STRING_VALUE:
                raise Hl7Error("100", "OBX-5 too long")
            value_text = raw_value
        obx14 = obx.get(14)
        observed = parse_dtm(_comp(s, obx14, 1)) if obx14 else fallback_time
        if observed is None:
            raise Hl7Error("101", "no observation time")
        observations.append(
            Observation(
                seq=i,
                code_system=_SYSTEM_FROM_HL7.get(system_raw, system_raw),
                code=code,
                code_text=_comp(s, obx.get(3), 2) or None,
                value_num=value_num,
                value_text=value_text,
                unit=unit,
                observed_at=observed,
                status=obx.get(11) or None,
                abnormal=obx.get(8) or None,
            )
        )
    if not observations:
        raise Hl7Error("101", "no OBX segments")
    return ParsedOru(msh=msh, pseudonym=pseudonym, observations=tuple(observations))


def serialize(msg: Message) -> str:
    fs = msg.seps.field
    lines = []
    for seg in msg.segments:
        if seg.name == "MSH":
            lines.append(fs.join(["MSH", *seg.fields[1:]]))
        else:
            lines.append(fs.join([seg.name, *seg.fields]))
    return "\r".join(lines) + "\r"


def scrub_identifiers(text: str) -> tuple[str, int]:
    """Data minimisation before anything is persisted: blank every PID field except
    PID-1/PID-3, drop NK1/GT1/IN* segments, normalise MSH-18 to UTF-8.
    Returns (scrubbed text, number of fields/segments dropped)."""
    msg = parse_message(text)
    dropped = 0
    out: list[Segment] = []
    for seg in msg.segments:
        if seg.name in _DROP_SEGMENTS:
            dropped += 1
            continue
        if seg.name == "PID":
            fields = []
            for i, v in enumerate(seg.fields, start=1):
                if i in _PID_KEEP or not v:
                    fields.append(v)
                else:
                    fields.append("")
                    dropped += 1
            seg = Segment("PID", tuple(fields))
        elif seg.name == "MSH":
            fields = list(seg.fields)
            fields.extend([""] * (18 - len(fields)))
            fields[17] = "UNICODE UTF-8"
            seg = Segment("MSH", tuple(fields))
        out.append(seg)
    return serialize(Message(msg.seps, tuple(out))), dropped


def build_oru(
    *,
    control_id: str,
    sending_app: str,
    sending_facility: str,
    receiving_app: str,
    receiving_facility: str,
    processing_id: str,
    pseudonym: str,
    observations: Sequence[Observation],
    timestamp: datetime,
) -> str:
    s = Separators()

    def e(v: str) -> str:
        return escape(s, v)

    ts = _format_dtm(timestamp)
    msh = [
        s.field,
        s.comp + s.rep + s.esc + s.sub,
        e(sending_app),
        e(sending_facility),
        e(receiving_app),
        e(receiving_facility),
        ts,
        "",
        "ORU^R01^ORU_R01",
        e(control_id),
        e(processing_id),
        "2.5.1",
        "", "", "", "", "",
        "UNICODE UTF-8",
    ]  # fmt: skip
    first_obs = min((o.observed_at for o in observations), default=timestamp)
    lines = [
        Segment("MSH", tuple(msh)),
        Segment("PID", ("1", "", f"{e(pseudonym)}^^^CLINGATE^PI")),
        Segment("OBR", ("1", "", "", "PANEL^Observations^L", "", "", _format_dtm(first_obs))),
    ]
    for i, o in enumerate(observations, start=1):
        is_num = o.value_num is not None
        code = f"{e(o.code)}^{e(o.code_text or '')}^{e(_SYSTEM_TO_HL7.get(o.code_system, o.code_system))}"
        value = format(o.value_num, "f") if o.value_num is not None else e(o.value_text or "")
        lines.append(
            Segment(
                "OBX",
                (
                    str(i),
                    "NM" if is_num else "ST",
                    code,
                    "",
                    value,
                    e(o.unit or ""),
                    "",
                    e(o.abnormal or ""),
                    "",
                    "",
                    e(o.status or "F"),
                    "",
                    "",
                    _format_dtm(o.observed_at),
                ),
            )  # fmt: skip
        )
    return serialize(Message(s, tuple(lines)))


def build_ack(
    msh: Msh | None,
    code: str,
    *,
    control_id: str,
    text: str | None = None,
    error_code: str = "207",
    now: datetime | None = None,
) -> str:
    """ACK for an inbound message. `text` must be generic (never echo payload content)."""
    s = Separators()
    ts = _format_dtm(now or datetime.now(UTC))
    src = msh or Msh("", "", "", "", "", "", "UNKNOWN", "P", "2.5.1", "")
    header = [
        s.field,
        s.comp + s.rep + s.esc + s.sub,
        escape(s, src.receiving_app),
        escape(s, src.receiving_facility),
        escape(s, src.sending_app),
        escape(s, src.sending_facility),
        ts,
        "",
        "ACK^R01^ACK",
        escape(s, control_id),
        escape(s, src.processing_id or "P"),
        "2.5.1",
    ]
    lines = [
        Segment("MSH", tuple(header)),
        Segment("MSA", (code, escape(s, src.control_id or "UNKNOWN"))),
    ]
    if text:
        lines.append(Segment("ERR", ("", "", f"{error_code}^{escape(s, text)}^HL70357", "E")))
    return serialize(Message(s, tuple(lines)))


def parse_ack(text: str) -> Ack:
    msg = parse_message(text)
    msa = msg.first("MSA")
    if msa is None or msa.get(1) not in ("AA", "AE", "AR", "CA", "CE", "CR"):
        raise Hl7Error("100", "not an acknowledgement")
    err = msg.first("ERR")
    err_code = err_text = None
    if err is not None:
        err_code = _comp(msg.seps, err.get(3), 1) or None
        err_text = _comp(msg.seps, err.get(3), 2) or None
    return Ack(
        code=msa.get(1),
        ref_control_id=unescape(msg.seps, msa.get(2)),
        error_code=err_code,
        error_text=err_text,
    )
