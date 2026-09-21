from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, field_validator

from overdone.schemas.dto import _blank_as_none


class AmountKind(StrEnum):
    delta = "delta"
    absolute = "absolute"
    extra_sets = "extra_sets"


class DraftItem(BaseModel):
    name: str
    amount: float | None = None
    amount_kind: AmountKind | None = None
    amount_unit: Literal["lb", "kg"] | None = None
    sets: int | None = None
    reps: int | None = None

    @field_validator(
        "amount",
        "amount_kind",
        "amount_unit",
        "sets",
        "reps",
        mode="before",
    )
    @classmethod
    def optional_null_strings(cls, value: object) -> object:
        return _blank_as_none(value)


class ExtractDraft(BaseModel):
    kind: Literal["single_session", "macro_goal"]
    weeks: int | None = None
    declared_fatigue: str | None = None
    asks_substitution: bool = False
    items: list[DraftItem]

    @field_validator("weeks", "declared_fatigue", mode="before")
    @classmethod
    def optional_null_strings(cls, value: object) -> object:
        return _blank_as_none(value)
