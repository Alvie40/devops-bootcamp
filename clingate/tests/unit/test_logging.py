from __future__ import annotations

import json
import logging

from clingate_lib.logging import SafeJsonFormatter


def _format(**kw) -> dict:
    rec = logging.LogRecord("t", logging.INFO, __file__, 1, "hello", None, kw.pop("exc_info", None))
    rec.ctx = kw
    return json.loads(SafeJsonFormatter().format(rec))


def test_H6_unknown_fields_are_dropped_and_named_not_valued():
    out = _format(request_id="r1", patient_name="SECRET", pseudonym="s1")
    assert out["request_id"] == "r1"
    assert "SECRET" not in json.dumps(out) and "s1" not in json.dumps(out)
    assert out["dropped_fields"] == ["patient_name", "pseudonym"]


def test_H6_exception_message_never_logged():
    try:
        raise ValueError("contains PHI: SECRET")
    except ValueError:
        import sys

        out = _format(exc_info=sys.exc_info())
    assert out["exc_type"] == "ValueError"
    assert "SECRET" not in json.dumps(out)
