"""Write tests/fixtures/golden_extract.json. Run once from backend/."""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "golden_extract.json"


def item(
    name: str,
    amount: float | None = None,
    kind: str | None = None,
    unit: str | None = None,
    sets: int | None = None,
    reps: int | None = None,
) -> dict:
    row: dict = {"name": name}
    if amount is not None:
        row["amount"] = amount
    if kind is not None:
        row["amount_kind"] = kind
    if unit is not None:
        row["amount_unit"] = unit
    if sets is not None:
        row["sets"] = sets
    if reps is not None:
        row["reps"] = reps
    return row


def session(*items: dict, fatigue: str | None = None, sub: bool = False) -> dict:
    draft: dict = {"kind": "single_session", "items": list(items)}
    if fatigue is not None:
        draft["declared_fatigue"] = fatigue
    if sub:
        draft["asks_substitution"] = True
    return draft


def macro(*items: dict, weeks: int) -> dict:
    return {"kind": "macro_goal", "weeks": weeks, "items": list(items)}


def row(id_: str, prompt: str, draft: dict, *, fewshot: bool = False) -> dict:
    payload = {"id": id_, "prompt": prompt, "draft": draft}
    if fewshot:
        payload["fewshot"] = True
    return payload


ROWS = [
    row(
        "rel-01",
        "add 20 lb to bench tomorrow",
        session(item("bench", 20, "delta", "lb")),
        fewshot=True,
    ),
    row(
        "abs-01",
        "bring pushdown up to 40 lb",
        session(item("pushdown", 40, "absolute", "lb")),
        fewshot=True,
    ),
    row(
        "rx-01",
        "3 sets of 8 @ 40lb on tricep pushdowns",
        session(item("tricep pushdowns", 40, "absolute", "lb", 3, 8)),
        fewshot=True,
    ),
    row(
        "macro-01",
        "i want to bench 225 by next month",
        macro(item("bench", 225, "absolute", "lb"), weeks=4),
        fewshot=True,
    ),
    row(
        "multi-01",
        "+10 bench, +5 incline, +3 sets pushdowns tomorrow",
        session(
            item("bench", 10, "delta", "lb"),
            item("incline", 5, "delta", "lb"),
            item("pushdowns", 3, "extra_sets"),
        ),
        fewshot=True,
    ),
    row(
        "nick-01",
        "bring OHP to 135 tomorrow",
        session(item("OHP", 135, "absolute", "lb")),
        fewshot=True,
    ),
    row(
        "fatigue-01",
        "only slept 4 hours and feel beat up, but I want to add 10 lbs to bench tomorrow",
        session(
            item("bench", 10, "delta", "lb"),
            fatigue="only slept 4 hours and feel beat up",
        ),
        fewshot=True,
    ),
    row(
        "sub-01",
        "i want to add 30 lbs to my bench press tomorrow, or tell me what to do instead",
        session(item("bench press", 30, "delta", "lb"), sub=True),
        fewshot=True,
    ),
    row(
        "nounit-01",
        "add 20 to bench tomorrow",
        session(item("bench", 20, "delta")),
        fewshot=True,
    ),
    row(
        "macro-delta-01",
        "add 30 lbs to my deadlift in 6 weeks",
        macro(item("deadlift", 30, "delta", "lb"), weeks=6),
        fewshot=True,
    ),
    row(
        "rel-squat-15",
        "bumping my squat up by 15 pounds next leg day",
        session(item("squat", 15, "delta", "lb")),
    ),
    row(
        "rel-kg",
        "throw an extra 5kg on overhead press",
        session(item("overhead press", 5, "delta", "kg")),
    ),
    row(
        "rel-sets",
        "i want to add 2 sets of pullups to my back workout friday",
        session(item("pullups", 2, "extra_sets")),
    ),
    row(
        "rel-incline-db",
        "gonna try adding 10lbs on incline db bench",
        session(item("incline db bench", 10, "delta", "lb")),
    ),
    row(
        "rel-drop",
        "drop 10 lbs off deadlift tomorrow",
        session(item("deadlift", -10, "delta", "lb")),
    ),
    row(
        "rel-dips",
        "tack on 5 lbs to weighted dips for my next chest session",
        session(item("weighted dips", 5, "delta", "lb")),
    ),
    row(
        "rel-laterals-kg",
        "increase lateral raises by 2.5kg next push workout",
        session(item("lateral raises", 2.5, "delta", "kg")),
    ),
    row(
        "rel-calf-set",
        "add 1 set of calf raises at the end of leg day",
        session(item("calf raises", 1, "extra_sets")),
    ),
    row(
        "rel-leg-press",
        "wanna add 25 pounds to my leg press on tuesday",
        session(item("leg press", 25, "delta", "lb")),
    ),
    row(
        "rel-db-shoulder",
        "can i add 5 lbs to DB shoulder press today?",
        session(item("DB shoulder press", 5, "delta", "lb")),
    ),
    row(
        "rel-rows-kg",
        "bumping up barbell rows by 10kg",
        session(item("barbell rows", 10, "delta", "kg")),
    ),
    row(
        "abs-bench",
        "i want to bench 225 tomorrow",
        session(item("bench", 225, "absolute", "lb")),
    ),
    row(
        "abs-squat-315",
        "squatting 315 on my next lower body day",
        session(item("squat", 315, "absolute", "lb")),
    ),
    row(
        "abs-dl-kg",
        "taking deadlift to 180kg for friday's heavy pull session",
        session(item("deadlift", 180, "absolute", "kg")),
    ),
    row(
        "abs-ohp-135",
        "want my overhead press at 135 lbs today",
        session(item("overhead press", 135, "absolute", "lb")),
    ),
    row(
        "abs-leg-ext",
        "set leg extension stack to 150 lbs for 3 sets",
        session(item("leg extension", 150, "absolute", "lb", sets=3)),
    ),
    row(
        "abs-db-80",
        "gonna work up to 80lb dumbbells on chest press",
        session(item("chest press", 80, "absolute", "lb")),
    ),
    row(
        "abs-cable-rows",
        "bring cable rows to 60kg next time",
        session(item("cable rows", 60, "absolute", "kg")),
    ),
    row(
        "abs-hip-thrust",
        "hit 100 lbs on hip thrusts tomorrow",
        session(item("hip thrusts", 100, "absolute", "lb")),
    ),
    row(
        "abs-curl-kg",
        "aiming for 50kg barbell curl on arms day",
        session(item("barbell curl", 50, "absolute", "kg")),
    ),
    row(
        "abs-pulldown",
        "moving my lat pulldown to 140 lbs next workout",
        session(item("lat pulldown", 140, "absolute", "lb")),
    ),
    row(
        "abs-db-90",
        "target 90 lb DBs on flat bench next week",
        session(item("flat bench", 90, "absolute", "lb")),
    ),
    row(
        "rx-4x5",
        "do 4x5 @ 275lbs squat tomorrow",
        session(item("squat", 275, "absolute", "lb", 4, 5)),
    ),
    row(
        "rx-5x5-kg",
        "5x5 bench press at 100kg next monday",
        session(item("bench press", 100, "absolute", "kg", 5, 5)),
    ),
    row(
        "rx-3x10-lp",
        "3x10 leg press 400 lbs on leg day",
        session(item("leg press", 400, "absolute", "lb", 3, 10)),
    ),
    row(
        "rx-1x3-dl",
        "want to hit 1 set of 3 @ 405lb deadlift RPE 9",
        session(item("deadlift", 405, "absolute", "lb", 1, 3)),
    ),
    row(
        "rx-flyes",
        "4 sets of 12 reps with 35lb dumbbells for incline flyes",
        session(item("incline flyes", 35, "absolute", "lb", 4, 12)),
    ),
    row(
        "rx-pulldown-kg",
        "3x15 @ 50kg lat pulldown today",
        session(item("lat pulldown", 50, "absolute", "kg", 3, 15)),
    ),
    row(
        "rx-ohp-5x3",
        "doing 5x3 at 145 lbs overhead press friday",
        session(item("overhead press", 145, "absolute", "lb", 5, 3)),
    ),
    row(
        "rx-db-bench-amrap-ignored",
        "2x8 @ 90lb db bench press then 1xAMRAP",
        session(item("db bench press", 90, "absolute", "lb", 2, 8)),
    ),
    row(
        "rx-cable-row",
        "3 sets 10 reps seated cable row at 120 pounds",
        session(item("seated cable row", 120, "absolute", "lb", 3, 10)),
    ),
    row(
        "rx-bss",
        "4x8 Bulgarian split squats @ 40lb dumbbells",
        session(item("Bulgarian split squats", 40, "absolute", "lb", 4, 8)),
    ),
    row(
        "rx-hamstring",
        "3x12 hamstring curls @ 110lbs on lower day",
        session(item("hamstring curls", 110, "absolute", "lb", 3, 12)),
    ),
    row(
        "macro-8w",
        "reach a 405 squat over the next 8 weeks",
        macro(item("squat", 405, "absolute", "lb"), weeks=8),
    ),
    row(
        "macro-100kg-bench",
        "hit 100kg bench press within 6 weeks",
        macro(item("bench press", 100, "absolute", "kg"), weeks=6),
    ),
    row(
        "macro-30-days",
        "get my squat from 275 to 315 in 30 days",
        macro(item("squat", 315, "absolute", "lb"), weeks=4),
    ),
    row(
        "macro-2-months-dips",
        "build up to 4 sets of 10 dips with +45lbs over 2 months",
        macro(item("dips", 45, "absolute", "lb", 4, 10), weeks=8),
    ),
    row(
        "macro-row-delta",
        "gain 15lbs on my barbell row baseline over the next 4 weeks",
        macro(item("barbell row", 15, "delta", "lb"), weeks=4),
    ),
    row(
        "multi-squat-rdl",
        "add 15 lbs to squat, 10 lbs to RDL, and 2 sets of leg curls",
        session(
            item("squat", 15, "delta", "lb"),
            item("RDL", 10, "delta", "lb"),
            item("leg curls", 2, "extra_sets"),
        ),
    ),
    row(
        "multi-prescriptions",
        "tomorrow: 225x5 bench, 80x8 db incline, and 50lb cable flyes",
        session(
            item("bench", 225, "absolute", "lb", reps=5),
            item("db incline", 80, "absolute", "lb", reps=8),
            item("cable flyes", 50, "absolute", "lb"),
        ),
    ),
    row(
        "multi-dl-ohp",
        "bumping up deadlift by 20 lbs and overhead press by 5 lbs on friday",
        session(
            item("deadlift", 20, "delta", "lb"),
            item("overhead press", 5, "delta", "lb"),
        ),
    ),
    row(
        "multi-mixed-units",
        "add 1 set to pullups, +5kg on barbell row, and +10lbs on lat pulldown",
        session(
            item("pullups", 1, "extra_sets"),
            item("barbell row", 5, "delta", "kg"),
            item("lat pulldown", 10, "delta", "lb"),
        ),
    ),
    row(
        "multi-leg-press-calf",
        "increase leg press to 450, add 10 lbs to calf raises, +1 set leg extensions",
        session(
            item("leg press", 450, "absolute", "lb"),
            item("calf raises", 10, "delta", "lb"),
            item("leg extensions", 1, "extra_sets"),
        ),
    ),
    row(
        "multi-arms",
        "+5 lbs db curls, +10 lbs hammer curls, +2 sets tricep extensions for arms",
        session(
            item("db curls", 5, "delta", "lb"),
            item("hammer curls", 10, "delta", "lb"),
            item("tricep extensions", 2, "extra_sets"),
        ),
    ),
    row(
        "multi-powerlifting",
        "wanna do 315 squat, 225 bench, and 405 deadlift in one session",
        session(
            item("squat", 315, "absolute", "lb"),
            item("bench", 225, "absolute", "lb"),
            item("deadlift", 405, "absolute", "lb"),
        ),
    ),
    row(
        "multi-signed",
        "add 10lb to overhead press and subtract 5lb from lateral raises",
        session(
            item("overhead press", 10, "delta", "lb"),
            item("lateral raises", -5, "delta", "lb"),
        ),
    ),
    row(
        "multi-bench-dips",
        "bumping bench press by 5kg and adding 2 sets of dips tomorrow",
        session(
            item("bench press", 5, "delta", "kg"),
            item("dips", 2, "extra_sets"),
        ),
    ),
    row(
        "multi-front-squat",
        "+10 lbs on front squat, +15 lbs on hip thrust, and 1 extra set of split squats",
        session(
            item("front squat", 10, "delta", "lb"),
            item("hip thrust", 15, "delta", "lb"),
            item("split squats", 1, "extra_sets"),
        ),
    ),
    row(
        "multi-back",
        "take lat pulldown to 150lb, facepulls to 60lb, and add 2 sets of shrugs",
        session(
            item("lat pulldown", 150, "absolute", "lb"),
            item("facepulls", 60, "absolute", "lb"),
            item("shrugs", 2, "extra_sets"),
        ),
    ),
    row(
        "nick-db",
        "add 10 lbs to DB bench",
        session(item("DB bench", 10, "delta", "lb")),
    ),
    row(
        "nick-rdl",
        "add 20 lbs on RDLs for leg day",
        session(item("RDLs", 20, "delta", "lb")),
    ),
    row(
        "nick-bb-row",
        "+15 lbs to BB row",
        session(item("BB row", 15, "delta", "lb")),
    ),
    row(
        "nick-rear-delts",
        "3 sets of 10 on rear delts",
        session(item("rear delts", sets=3, reps=10)),
    ),
    row(
        "nick-conventional",
        "add 10kg on conventional",
        session(item("conventional", 10, "delta", "kg")),
    ),
    row(
        "nick-skullcrushers",
        "take skullcrushers up to 70 lbs",
        session(item("skullcrushers", 70, "absolute", "lb")),
    ),
    row(
        "nick-preacher",
        "do 4 sets of 12 on preacher curls",
        session(item("preacher curls", sets=4, reps=12)),
    ),
    row(
        "nick-sissy",
        "bump up sissy squats by 10 lbs",
        session(item("sissy squats", 10, "delta", "lb")),
    ),
    row(
        "nick-incline-dbs",
        "+5 lbs on incline DBs",
        session(item("incline DBs", 5, "delta", "lb")),
    ),
    row(
        "nick-hammy",
        "add 2 sets to hammy curls",
        session(item("hammy curls", 2, "extra_sets")),
    ),
    row(
        "nick-incline-bb",
        "bring incline barbell up to 185",
        session(item("incline barbell", 185, "absolute")),
    ),
    row(
        "nick-pec-deck",
        "add 10 lbs on pec deck tomorrow",
        session(item("pec deck", 10, "delta", "lb")),
    ),
    row(
        "fatigue-sore",
        "feeling super sore from tuesday, but wanna try adding 5kg to squat today",
        session(
            item("squat", 5, "delta", "kg"),
            fatigue="feeling super sore from tuesday",
        ),
    ),
    row(
        "fatigue-work",
        "exhausted from work and low energy, aiming for 225 bench anyway",
        session(
            item("bench", 225, "absolute", "lb"),
            fatigue="exhausted from work and low energy",
        ),
    ),
    row(
        "fatigue-sleep",
        "slept terrible last night, can i still add 15 lbs to deadlift?",
        session(
            item("deadlift", 15, "delta", "lb"),
            fatigue="slept terrible last night",
        ),
    ),
    row(
        "fatigue-back",
        "lower back is stiff today, wanting to do 315 squat",
        session(
            item("squat", 315, "absolute", "lb"),
            fatigue="lower back is stiff today",
        ),
    ),
    row(
        "fatigue-weather",
        "feeling under the weather, adding 5lbs to overhead press",
        session(
            item("overhead press", 5, "delta", "lb"),
            fatigue="feeling under the weather",
        ),
    ),
    row(
        "fatigue-shoulder",
        "shoulder feels a bit twingey, but wanna bump incline db bench to 70s",
        session(
            item("incline db bench", 70, "absolute", "lb"),
            fatigue="shoulder feels a bit twingey",
        ),
    ),
    row(
        "fatigue-cns",
        "drained from CNS fatigue from yesterday's heavy pull, adding 2 sets of squats tomorrow",
        session(
            item("squats", 2, "extra_sets"),
            fatigue="drained from CNS fatigue from yesterday's heavy pull",
        ),
    ),
    row(
        "fatigue-fasted",
        "fasted today and energy is low, bring pushdowns up to 50 lbs",
        session(
            item("pushdowns", 50, "absolute", "lb"),
            fatigue="fasted today and energy is low",
        ),
    ),
    row(
        "fatigue-3h",
        "working on 3 hours of sleep, add 20 lbs to leg press",
        session(
            item("leg press", 20, "delta", "lb"),
            fatigue="working on 3 hours of sleep",
        ),
    ),
    row(
        "fatigue-elbow",
        "elbow aching slightly, wanna add 5 lbs to barbell curl",
        session(
            item("barbell curl", 5, "delta", "lb"),
            fatigue="elbow aching slightly",
        ),
    ),
    row(
        "fatigue-knee",
        "knee feels cranky, but planning 4x8 @ 245lb squat",
        session(
            item("squat", 245, "absolute", "lb", 4, 8),
            fatigue="knee feels cranky",
        ),
    ),
    row(
        "sub-ohp",
        "add 20 lbs to overhead press, but if that's overdoing it what exercise should i swap to?",
        session(item("overhead press", 20, "delta", "lb"), sub=True),
    ),
    row(
        "sub-squat",
        "bring squat to 365, or give me a safer alternative lower body move",
        session(item("squat", 365, "absolute", "lb"), sub=True),
    ),
    row(
        "sub-rows",
        "+15 lbs on barbell rows tomorrow, or suggest a safer back exercise if too high",
        session(item("barbell rows", 15, "delta", "lb"), sub=True),
    ),
    row(
        "sub-dips",
        "add 3 extra heavy sets of dips, or tell me a better chest finisher",
        session(item("dips", 3, "extra_sets"), sub=True),
    ),
    row(
        "sub-dl",
        "jump deadlift by 40 lbs friday, or what should i do instead?",
        session(item("deadlift", 40, "delta", "lb"), sub=True),
    ),
    row(
        "sub-incline-kg",
        "add 10kg to incline db press, or offer a safer substitute",
        session(item("incline db press", 10, "delta", "kg"), sub=True),
    ),
    row(
        "sub-leg-press",
        "take leg press to 500 lbs tomorrow, or advise a safer set/rep scheme",
        session(item("leg press", 500, "absolute", "lb"), sub=True),
    ),
    row(
        "sub-skull",
        "+10 lbs on skullcrushers, or suggest another tricep exercise if my elbows will complain",
        session(item("skullcrushers", 10, "delta", "lb"), sub=True),
    ),
    row(
        "sub-bench-week",
        "aiming for 225 bench press next week, or recommend a better progression plan",
        session(item("bench press", 225, "absolute", "lb"), sub=True),
    ),
    row(
        "sub-rdl",
        "add 25 lbs on RDLs tomorrow or recommend a safer posterior chain exercise",
        session(item("RDLs", 25, "delta", "lb"), sub=True),
    ),
    row(
        "sub-shoulder-db",
        "bring shoulder press to 80lb DBs or tell me what to swap it with",
        session(item("shoulder press", 80, "absolute", "lb"), sub=True),
    ),
    row(
        "nounit-pushdown",
        "bring pushdown up to 40",
        session(item("pushdown", 40, "absolute")),
    ),
    row(
        "nounit-squat",
        "take squat to 315 next leg day",
        session(item("squat", 315, "absolute")),
    ),
    row(
        "nounit-ohp-delta",
        "bumping overhead press by 10 on friday",
        session(item("overhead press", 10, "delta")),
    ),
    row(
        "nounit-bench-reps",
        "want to hit 225 for 5 reps on bench",
        session(item("bench", 225, "absolute", reps=5)),
    ),
    row(
        "nounit-laterals",
        "add 5 to lateral raises",
        session(item("lateral raises", 5, "delta")),
    ),
    row(
        "nounit-dl",
        "take deadlift to 405 next week",
        session(item("deadlift", 405, "absolute")),
    ),
    row(
        "nounit-rows",
        "bumping barbell rows up by 15",
        session(item("barbell rows", 15, "delta")),
    ),
    row(
        "nounit-rx",
        "3 sets of 8 @ 50 on cable rows",
        session(item("cable rows", 50, "absolute", sets=3, reps=8)),
    ),
    row(
        "nounit-lp",
        "add 25 to leg press on tuesday",
        session(item("leg press", 25, "delta")),
    ),
    row(
        "nounit-db-80s",
        "bring db bench up to 80s",
        session(item("db bench", 80, "absolute")),
    ),
    row(
        "nounit-pulldown",
        "increase lat pulldown by 10 tomorrow",
        session(item("lat pulldown", 10, "delta")),
    ),
    row(
        "edge-dense-multi",
        "add 10lbs to DB incline bench press, 5lbs on lateral raises and do 3 sets of 12 pushdowns @ 40lbs",
        session(
            item("DB incline bench press", 10, "delta", "lb"),
            item("lateral raises", 5, "delta", "lb"),
            item("pushdowns", 40, "absolute", "lb", 3, 12),
        ),
    ),
    row(
        "edge-question",
        "can i add 15 lbs to my bench press or is that too much?",
        session(item("bench press", 15, "delta", "lb")),
    ),
    row(
        "edge-runon",
        "im thinking of adding 10 lbs to my bench but my shoulder has been kinda iffy since last week",
        session(
            item("bench", 10, "delta", "lb"),
            fatigue="shoulder has been kinda iffy since last week",
        ),
    ),
    row(
        "edge-jump-macro",
        "jump from 185 to 205 on incline barbell in 2 weeks",
        macro(item("incline barbell", 205, "absolute", "lb"), weeks=2),
    ),
    row(
        "edge-mixed-lifts",
        "add 5kg to bench and do 4x10 @ 60kg squat next leg day",
        session(
            item("bench", 5, "delta", "kg"),
            item("squat", 60, "absolute", "kg", 4, 10),
        ),
    ),
    row(
        "get-to-macro",
        "I want to get to 3 sets of 8 @ 40lb on my cable pushdown over the next 4 weeks",
        macro(item("cable pushdown", 40, "absolute", "lb", 3, 8), weeks=4),
    ),
]


def main() -> None:
    ids = [item["id"] for item in ROWS]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate gold ids")
    OUT.write_text(json.dumps(ROWS, indent=2) + "\n")
    print(f"wrote {len(ROWS)} rows to {OUT}")


if __name__ == "__main__":
    main()
