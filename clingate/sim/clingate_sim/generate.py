"""Seeded, deterministic synthetic data. Nothing here is real PHI. Identifier fields carry
obviously fake values so the scrubbing path is exercised."""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from clingate_lib import hl7
from clingate_lib.model import Observation

_EPOCH = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


def _observations(rng: random.Random, n_obs: int, base: datetime) -> list[Observation]:
    out = []
    for i in range(1, n_obs + 1):
        out.append(
            Observation(
                seq=i,
                code_system="LOINC",
                code="8867-4",
                code_text="Heart rate",
                value_num=Decimal(rng.randint(50, 110)),
                unit="/min",
                observed_at=base + timedelta(seconds=i),
            )
        )
    return out


def hl7_message(
    seed: int, n: int, *, sending_app: str = "LABAPP", sending_facility: str = "LAB1",
    processing_id: str = "T", n_obs: int = 12, with_identifiers: bool = True,
) -> tuple[str, str]:  # fmt: skip
    """Returns (idempotency_key = MSH-10, ER7 text)."""
    rng = random.Random(f"{seed}-{n}")
    control_id = f"S{seed}-M{n:08d}"
    text = hl7.build_oru(
        control_id=control_id,
        sending_app=sending_app,
        sending_facility=sending_facility,
        receiving_app="CLINGATE",
        receiving_facility="CLINGATE",
        processing_id=processing_id,
        pseudonym=f"subj-{rng.randint(1, 5000):05d}",
        observations=_observations(rng, n_obs, _EPOCH + timedelta(minutes=n)),
        timestamp=_EPOCH,
    )
    if with_identifiers:
        msg = hl7.parse_message(text)
        segs = []
        for s in msg.segments:
            if s.name == "PID":
                f = list(s.fields) + [""] * (11 - len(s.fields))
                f[4], f[6], f[10] = "SINTETICO^PACIENTE", "19700101", "RUA FALSA 1^^CIDADE"
                s = hl7.Segment("PID", tuple(f))
            segs.append(s)
        text = hl7.serialize(hl7.Message(msg.seps, tuple(segs)))
    return control_id, text


def device_batch(seed: int, n: int, *, n_obs: int = 30) -> tuple[str, bytes]:
    """Returns (idempotency_key = batch_id, JSON body)."""
    rng = random.Random(f"{seed}-{n}")
    batch_id = f"b{seed:04d}-{n:010d}"
    base = _EPOCH + timedelta(minutes=n)
    body = {
        "schema_version": "1",
        "batch_id": batch_id,
        "device_id": f"dev-{rng.randint(1, 2000):06d}",
        "subject_ref": f"subj-{rng.randint(1, 2000):05d}",
        "sequence": n,
        "sent_at": base.isoformat(),
        "observations": [
            {
                "code": "8867-4",
                "system": "LOINC",
                "value": rng.randint(50, 110),
                "unit": "/min",
                "observed_at": (base + timedelta(seconds=i)).isoformat(),
            }
            for i in range(n_obs)
        ],
    }
    return batch_id, json.dumps(body, separators=(",", ":")).encode()
