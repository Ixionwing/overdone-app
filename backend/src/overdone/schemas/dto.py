from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class TrafficLight(StrEnum):
    green = "green"
    yellow = "yellow"
    red = "red"


class PromptKind(StrEnum):
    single_session = "single_session"
    macro_goal = "macro_goal"


class HaltReason(StrEnum):
    missing_baseline = "missing_baseline"
    missing_exercise = "missing_exercise"
    ambiguous_units = "ambiguous_units"
    extract_failed = "extract_failed"


class Unit(StrEnum):
    lb = "lb"
    kg = "kg"


def _blank_as_none(value: object) -> object:
    if isinstance(value, str) and value.strip().casefold() in {"", "null", "none"}:
        return None
    return value


class LogSet(BaseModel):
    exercise_id: str | None = None
    exercise_name: str
    weight_kg: float
    reps: int
    sets: int = 1


class SessionLog(BaseModel):
    logged_on: date
    notes: str | None = None
    sets: list[LogSet]


class Benchmark(BaseModel):
    exercise_id: str | None = None
    exercise_name: str
    one_rm_kg: float


class Baseline(BaseModel):
    preferred_unit: Unit = Unit.lb
    benchmarks: list[Benchmark] = Field(default_factory=list)
    sessions: list[SessionLog] = Field(default_factory=list)


class ProposedItem(BaseModel):
    exercise_name: str
    exercise_id: str | None = None
    weight_kg: float | None = None
    delta_kg: float | None = None
    reps: int | None = None
    sets: int | None = None
    extra_sets: int | None = None


class ExtractedPrompt(BaseModel):
    kind: PromptKind
    items: list[ProposedItem]
    target_date: date | None = None
    weeks: int | None = None
    target_weight_kg: float | None = None
    target_exercise_name: str | None = None
    declared_fatigue: str | None = None
    asks_substitution: bool = False
    unit: Unit | None = None
    raw_text: str = ""


class FactorScores(BaseModel):
    volume_jump_pct: float
    axial_compression: float
    cns_index: float
    joint_vectors: dict[str, float]


class ItemVerdict(BaseModel):
    exercise_id: str
    exercise_name: str
    light: TrafficLight
    factors: FactorScores
    narrative: str
    catalog_source_id: str | None = None


class WarningFlag(BaseModel):
    kind: str
    message: str
    source_id: str | None = None


class Halt(BaseModel):
    reason: HaltReason
    message: str
    exercise_name: str | None = None


class EvaluationResult(BaseModel):
    halted: Halt | None = None
    overall_light: TrafficLight | None = None
    items: list[ItemVerdict] = Field(default_factory=list)
    session_factors: FactorScores | None = None
    narrative: str | None = None
    warnings: list[WarningFlag] = Field(default_factory=list)


class ExerciseEnrichment(BaseModel):
    axial_factor: float
    cns_factor: float
    joints: dict[str, float]


DEFAULT_ENRICHMENT = ExerciseEnrichment(
    axial_factor=0.15,
    cns_factor=0.25,
    joints={"shoulder": 0.4, "knee": 0.1, "spine": 0.15, "elbow": 0.2},
)
