from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ImportSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exercise: str
    weight: float
    reps: int
    sets: int = 1
    unit: str | None = None
    exercise_id: str | None = None


class ImportSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    notes: str | None = None
    sets: list[ImportSet] = Field(default_factory=list)


class ImportBenchmark(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exercise: str
    one_rm: float
    unit: str | None = None
    exercise_id: str | None = None


class BaselineImport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preferred_unit: str = "lb"
    benchmarks: list[ImportBenchmark] = Field(default_factory=list)
    sessions: list[ImportSession] = Field(default_factory=list)

    @field_validator("preferred_unit")
    @classmethod
    def unit_ok(cls, value: str) -> str:
        if value not in {"lb", "kg"}:
            raise ValueError("preferred_unit must be lb or kg")
        return value


class BaselineTextImport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str


class BaselineStatus(BaseModel):
    preferred_unit: str
    benchmark_count: int
    session_count: int
    set_count: int
    baseline: BaselineImport


class EvaluateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str

    @field_validator("prompt")
    @classmethod
    def prompt_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("prompt must not be empty")
        return stripped
