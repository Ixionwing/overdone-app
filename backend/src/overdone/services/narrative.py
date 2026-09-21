from overdone.schemas.dto import (
    FactorScores,
    ItemVerdict,
    TrafficLight,
    WarningFlag,
)

_SCOPE = "Diagnostic evaluation complete; exercise substitution is outside scope."


def _dominant_factor(factors: FactorScores) -> str:
    joints = factors.joint_vectors
    top_joint = max(joints, key=lambda name: joints[name]) if joints else None
    candidates = {
        "volume": abs(factors.volume_jump_pct),
        "axial": abs(factors.axial_compression),
        "cns": abs(factors.cns_index),
    }
    if top_joint:
        candidates[f"joint:{top_joint}"] = abs(joints[top_joint])
    return max(candidates, key=lambda name: candidates[name])


def session_narrative(
    overall: TrafficLight,
    items: list[ItemVerdict],
    factors: FactorScores,
) -> str:
    names = ", ".join(item.exercise_name for item in items)
    dominant = _dominant_factor(factors)
    first = (
        f"Overall session risk is {overall.value} for {names}, "
        f"with a {factors.volume_jump_pct:.1f}% volume jump driven by {dominant}"
    )
    second = (
        f"The load change is {overall.value} relative to the last working sets "
        "and is a diagnostic readout only"
    )
    return f"{first}. {second}."


def macro_narrative(verdict: ItemVerdict, weeks: int, *, sets: int, reps: int) -> str:
    first = (
        f"{verdict.exercise_name} over {weeks} weeks is {verdict.light.value} "
        f"against historical adaptation velocity"
    )
    second = (
        f"Implied volume jump to a {sets}x{reps} at the target is "
        f"{verdict.factors.volume_jump_pct:.1f}% and this is a feasibility "
        "readout, not a programmed progression"
    )
    return f"{first}. {second}."


def scope_disclaimer() -> WarningFlag:
    return WarningFlag(kind="scope_disclaimer", message=_SCOPE, source_id=None)
