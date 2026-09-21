from overdone.schemas.dto import (
    FactorScores,
    ItemVerdict,
    TrafficLight,
    WarningFlag,
)
from overdone.services.narrative import (
    macro_narrative,
    scope_disclaimer,
    session_narrative,
)


def test_session_narrative_includes_light_and_volume():
    items = [
        ItemVerdict(
            exercise_id="bench",
            exercise_name="Bench",
            light=TrafficLight.yellow,
            factors=FactorScores(
                volume_jump_pct=10.8,
                axial_compression=1.0,
                cns_index=1.0,
                joint_vectors={"shoulder": 1.0},
            ),
            narrative="",
        )
    ]
    factors = FactorScores(
        volume_jump_pct=10.8,
        axial_compression=1.0,
        cns_index=1.0,
        joint_vectors={"shoulder": 1.0},
    )
    text = session_narrative(TrafficLight.yellow, items, factors)
    sentences = [part.strip() for part in text.split(".") if part.strip()]
    assert 2 <= len(sentences) <= 3
    assert "yellow" in text.lower()
    assert "10.8" in text
    assert "Bench" in text


def test_macro_narrative_states_feasibility():
    verdict = ItemVerdict(
        exercise_id="squat",
        exercise_name="Squat",
        light=TrafficLight.red,
        factors=FactorScores(
            volume_jump_pct=40.0,
            axial_compression=1.0,
            cns_index=1.0,
            joint_vectors={},
        ),
        narrative="",
    )
    text = macro_narrative(verdict, weeks=4, sets=3, reps=5)
    assert "red" in text.lower()
    assert "4" in text
    assert "Squat" in text
    assert "3x5" in text


def test_macro_narrative_names_3x8_prescription():
    verdict = ItemVerdict(
        exercise_id="pushdown",
        exercise_name="Cable Pushdown",
        light=TrafficLight.green,
        factors=FactorScores(
            volume_jump_pct=-6.7,
            axial_compression=1.0,
            cns_index=1.0,
            joint_vectors={},
        ),
        narrative="",
    )
    text = macro_narrative(verdict, weeks=4, sets=3, reps=8)
    assert "3x8" in text
    assert "3x5" not in text
    assert "-6.7" in text


def test_scope_disclaimer_copy():
    flag = scope_disclaimer()
    assert flag == WarningFlag(
        kind="scope_disclaimer",
        message=(
            "Diagnostic evaluation complete; exercise substitution is outside scope."
        ),
        source_id=None,
    )
