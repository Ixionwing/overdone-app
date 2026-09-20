import inspect

from overdone.schemas.dto import (
    DEFAULT_ENRICHMENT,
    ExerciseEnrichment,
    LogSet,
    ProposedItem,
    TrafficLight,
)
from overdone.services.scoring import score_macro, score_session
from overdone.services.units import lb_to_kg


def _bench_last() -> LogSet:
    return LogSet(
        exercise_id="bench",
        exercise_name="Bench",
        weight_kg=lb_to_kg(185),
        reps=5,
        sets=4,
    )


def _press_enrichment() -> dict[str, ExerciseEnrichment]:
    return {"bench": DEFAULT_ENRICHMENT, "row": DEFAULT_ENRICHMENT}


def test_plus_20lb_bench_volume_jump_is_yellow_band():
    items = [
        ProposedItem(
            exercise_name="Bench",
            exercise_id="bench",
            delta_kg=lb_to_kg(20),
        )
    ]
    overall, verdicts, _factors = score_session(
        items, {"bench": _bench_last()}, _press_enrichment()
    )
    assert round(verdicts[0].factors.volume_jump_pct, 1) == 10.8
    assert verdicts[0].light is TrafficLight.yellow
    assert overall is TrafficLight.yellow


def test_plus_500lb_bench_is_red_with_extreme_volume_jump():
    items = [
        ProposedItem(
            exercise_name="Bench",
            exercise_id="bench",
            delta_kg=lb_to_kg(500),
        )
    ]
    overall, verdicts, _factors = score_session(
        items, {"bench": _bench_last()}, _press_enrichment()
    )
    assert round(verdicts[0].factors.volume_jump_pct, 1) == 270.3
    assert verdicts[0].light is TrafficLight.red
    assert overall is TrafficLight.red


def test_session_overall_worse_than_items_when_cns_stacks():
    last_a = LogSet(exercise_id="a", exercise_name="A", weight_kg=100, reps=5, sets=5)
    last_b = LogSet(exercise_id="b", exercise_name="B", weight_kg=100, reps=5, sets=5)
    items = [
        ProposedItem(exercise_name="A", exercise_id="a", weight_kg=108),
        ProposedItem(exercise_name="B", exercise_id="b", weight_kg=108),
    ]
    high_cns = ExerciseEnrichment(
        axial_factor=0.15, cns_factor=0.85, joints={"spine": 0.15}
    )
    overall, verdicts, _factors = score_session(
        items, {"a": last_a, "b": last_b}, {"a": high_cns, "b": high_cns}
    )
    assert all(item.light is TrafficLight.green for item in verdicts)
    assert overall is TrafficLight.yellow


def test_macro_225_in_4_weeks_with_zero_velocity_is_red():
    working = _bench_last()
    verdict = score_macro(
        current_kg=working.weight_kg,
        target_kg=lb_to_kg(225),
        weeks=4,
        weekly_velocity_kg=0.0,
        working=working,
        enrichment=DEFAULT_ENRICHMENT,
    )
    assert verdict.light is TrafficLight.red


def test_qualitative_notes_do_not_change_volume_jump():
    assert "notes" not in inspect.signature(score_session).parameters
