"""Device batch schema v1 (see docs/SPEC.md 5.1)."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    model_validator,
)

from .model import Observation, ParsedPayload

_ID = r"^[A-Za-z0-9._-]{1,64}$"
Number = Annotated[float, Field(allow_inf_nan=False, strict=True)]


class ObservationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=64)
    system: str = Field(min_length=1, max_length=32)
    value: StrictInt | Number | StrictStr
    unit: str | None = Field(default=None, max_length=32)
    observed_at: AwareDatetime

    @model_validator(mode="after")
    def _numeric_needs_unit(self) -> ObservationIn:
        if not isinstance(self.value, str) and not self.unit:
            raise ValueError("unit required for numeric value")
        if isinstance(self.value, str) and len(self.value) > 2000:
            raise ValueError("text value too long")
        return self


class BatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"]
    batch_id: str = Field(pattern=_ID)
    device_id: str = Field(pattern=_ID)
    subject_ref: str = Field(pattern=_ID)
    sequence: int = Field(ge=0)
    sent_at: AwareDatetime
    observations: list[ObservationIn] = Field(min_length=1, max_length=1000)


def parse_batch(raw: bytes) -> ParsedPayload:
    batch = BatchIn.model_validate_json(raw)
    obs = []
    for i, o in enumerate(batch.observations, start=1):
        numeric = not isinstance(o.value, str)
        obs.append(
            Observation(
                seq=i,
                code_system=o.system,
                code=o.code,
                observed_at=o.observed_at,
                value_num=Decimal(str(o.value)) if numeric else None,
                value_text=None if numeric else str(o.value),
                unit=o.unit,
            )
        )
    return ParsedPayload(batch.subject_ref, batch.device_id, tuple(obs))
