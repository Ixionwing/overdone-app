from __future__ import annotations

from overdone.schemas.dto import ExtractedPrompt, PromptKind, ProposedItem, Unit
from overdone.services.units import lb_to_kg

LB = lb_to_kg


def _session(
    *items: ProposedItem,
    unit: Unit | None = Unit.lb,
    declared_fatigue: str | None = None,
    asks_substitution: bool = False,
) -> ExtractedPrompt:
    return ExtractedPrompt(
        kind=PromptKind.single_session,
        items=list(items),
        unit=unit,
        declared_fatigue=declared_fatigue,
        asks_substitution=asks_substitution,
        raw_text="",
    )


def _macro(
    name: str,
    pounds: float,
    *,
    weeks: int = 4,
) -> ExtractedPrompt:
    return ExtractedPrompt(
        kind=PromptKind.macro_goal,
        items=[],
        weeks=weeks,
        target_weight_kg=LB(pounds),
        target_exercise_name=name,
        unit=Unit.lb,
        raw_text="",
    )


DEFAULT_PROMPTS: dict[str, ExtractedPrompt] = {
    "I want to add 20 lbs to my bench press tomorrow": _session(
        ProposedItem(exercise_name="Bench", delta_kg=LB(20))
    ),
    "Tomorrow: +10 lbs Bench, +5 lbs Incline DB Press, +3 sets Pushdowns.": _session(
        ProposedItem(exercise_name="Bench", delta_kg=LB(10)),
        ProposedItem(exercise_name="Incline DB Press", delta_kg=LB(5)),
        ProposedItem(exercise_name="Pushdowns", extra_sets=3),
    ),
    "Reach a 225 lb Squat by next month.": _macro("Squat", 225),
    "I want to bring my cable pushdown up to 40 lbs": _session(
        ProposedItem(exercise_name="cable pushdown", weight_kg=LB(40))
    ),
    "I want to bring my cable pushdown up to 40 lbs in a month": _macro(
        "cable pushdown", 40
    ),
    "4 sets of 185 lb Overhead Press tomorrow.": _session(
        ProposedItem(
            exercise_name="Overhead Press",
            weight_kg=LB(185),
            sets=4,
        )
    ),
    "Add 200 to Bench tomorrow.": _session(
        ProposedItem(exercise_name="Bench", delta_kg=200),
        unit=None,
    ),
    "Slept 4 hours, but want to add 10 lbs to Bench tomorrow.": _session(
        ProposedItem(exercise_name="Bench", delta_kg=LB(10)),
        declared_fatigue="Slept 4 hours",
    ),
    "Add 30 lbs to Bench tomorrow, or tell me what to do instead.": _session(
        ProposedItem(exercise_name="Bench", delta_kg=LB(30)),
        asks_substitution=True,
    ),
    "Add 20 lbs to Bench tomorrow.": _session(
        ProposedItem(exercise_name="Bench", delta_kg=LB(20))
    ),
    "Add 20 lbs to medium grip barbell bench tomorrow.": _session(
        ProposedItem(exercise_name="medium grip barbell bench", delta_kg=LB(20))
    ),
}


class ScriptedExtractClient:
    def __init__(self, mapping: dict[str, ExtractedPrompt] | None = None) -> None:
        self.mapping = mapping or DEFAULT_PROMPTS

    async def extract(self, text: str) -> ExtractedPrompt:
        found = self.mapping.get(text)
        if found is None:
            return ExtractedPrompt(
                kind=PromptKind.single_session, items=[], raw_text=text
            )
        return found.model_copy(update={"raw_text": text})
