from fastapi.testclient import TestClient

RICH = {
    "preferred_unit": "lb",
    "benchmarks": [
        {
            "exercise": "Barbell Bench Press - Medium Grip",
            "one_rm": 225,
            "unit": "lb",
        }
    ],
    "sessions": [
        {
            "date": "2026-09-13",
            "notes": "Right shoulder felt tight on set 3",
            "sets": [
                {
                    "exercise": "Barbell Bench Press - Medium Grip",
                    "weight": 185,
                    "unit": "lb",
                    "reps": 5,
                    "sets": 4,
                },
                {
                    "exercise": "Incline Dumbbell Press",
                    "weight": 50,
                    "unit": "lb",
                    "reps": 8,
                    "sets": 3,
                },
                {
                    "exercise": "Cable Pushdown",
                    "weight": 40,
                    "unit": "lb",
                    "reps": 12,
                    "sets": 3,
                },
                {
                    "exercise": "Barbell Squat",
                    "weight": 185,
                    "unit": "lb",
                    "reps": 5,
                    "sets": 3,
                },
            ],
        }
    ],
}

MIXED = {
    "preferred_unit": "lb",
    "benchmarks": [],
    "sessions": [
        {
            "date": "2026-09-13",
            "notes": None,
            "sets": [
                {
                    "exercise": "Barbell Bench Press - Medium Grip",
                    "weight": 185,
                    "unit": "lb",
                    "reps": 5,
                    "sets": 4,
                },
                {
                    "exercise": "Barbell Squat",
                    "weight": 80,
                    "unit": "kg",
                    "reps": 5,
                    "sets": 3,
                },
            ],
        }
    ],
}


def _put(client: TestClient, payload: dict | None = None) -> None:
    response = client.put("/api/v1/baseline", json=payload or RICH)
    assert response.status_code == 200


def test_evaluate_empty_prompt_is_422(client: TestClient) -> None:
    response = client.post("/api/v1/evaluate", json={"prompt": "   "})
    assert response.status_code == 422


def test_plus_20lb_bench_returns_yellow_gauges(client: TestClient) -> None:
    _put(client)
    response = client.post(
        "/api/v1/evaluate",
        json={"prompt": "I want to add 20 lbs to my bench press tomorrow"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["halted"] is None
    assert body["overall_light"] == "yellow"
    assert len(body["items"]) == 1
    assert body["items"][0]["factors"]["volume_jump_pct"] == 10.8
    assert body["session_factors"]["volume_jump_pct"] == 10.8
    assert body["narrative"]
    assert "Right shoulder" not in (body["narrative"] or "")
    note = next(flag for flag in body["warnings"] if flag["kind"] == "qualitative_note")
    assert "Note from" in note["message"]
    assert "Right shoulder felt tight on set 3" in note["message"]


def test_multi_movement_itemizes_three(client: TestClient) -> None:
    _put(client)
    response = client.post(
        "/api/v1/evaluate",
        json={
            "prompt": (
                "Tomorrow: +10 lbs Bench, +5 lbs Incline DB Press, +3 sets Pushdowns."
            )
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["halted"] is None
    assert body["overall_light"] in {"green", "yellow", "red"}
    assert len(body["items"]) == 3
    names = " ".join(item["exercise_name"].casefold() for item in body["items"])
    assert "bench" in names
    assert "incline" in names
    assert "pushdown" in names


def test_macro_225_squat_next_month(client: TestClient) -> None:
    _put(client)
    response = client.post(
        "/api/v1/evaluate",
        json={"prompt": "Reach a 225 lb Squat by next month."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["halted"] is None
    assert body["overall_light"] == "red"
    assert "squat" in body["items"][0]["exercise_name"].casefold()
    assert "red" in (body["narrative"] or "").lower()


def test_ohp_without_history_halts_missing_exercise(client: TestClient) -> None:
    _put(client)
    response = client.post(
        "/api/v1/evaluate",
        json={"prompt": "4 sets of 185 lb Overhead Press tomorrow."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["halted"]["reason"] == "missing_exercise"
    assert body["overall_light"] is None


def test_mixed_units_without_unit_halt(client: TestClient) -> None:
    _put(client, MIXED)
    response = client.post(
        "/api/v1/evaluate", json={"prompt": "Add 200 to Bench tomorrow."}
    )
    assert response.status_code == 200
    assert response.json()["halted"]["reason"] == "ambiguous_units"


def test_fatigue_banner(client: TestClient) -> None:
    _put(client)
    response = client.post(
        "/api/v1/evaluate",
        json={"prompt": "Slept 4 hours, but want to add 10 lbs to Bench tomorrow."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["halted"] is None
    fatigue = next(
        flag for flag in body["warnings"] if flag["kind"] == "in_prompt_fatigue"
    )
    assert "slept 4 hours" in fatigue["message"].casefold()
    assert "User declared:" in fatigue["message"]


def test_substitution_disclaimer_still_scores(client: TestClient) -> None:
    _put(client)
    response = client.post(
        "/api/v1/evaluate",
        json={"prompt": "Add 30 lbs to Bench tomorrow, or tell me what to do instead."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["halted"] is None
    assert body["overall_light"] in {"yellow", "red"}
    kinds = {flag["kind"]: flag["message"] for flag in body["warnings"]}
    assert kinds["scope_disclaimer"] == (
        "Diagnostic evaluation complete; exercise substitution is outside scope."
    )


def test_plus_500lb_is_red_extreme_jump(client: TestClient) -> None:
    _put(client)
    response = client.post(
        "/api/v1/evaluate",
        json={"prompt": "Add 500 lbs to my Bench Press tomorrow."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["overall_light"] == "red"
    assert body["items"][0]["factors"]["volume_jump_pct"] == 270.3


def test_evaluate_does_not_insert_sessions(client: TestClient) -> None:
    _put(client)
    prompt = {"prompt": "I want to add 20 lbs to my bench press tomorrow"}
    first = client.post("/api/v1/evaluate", json=prompt)
    second = client.post("/api/v1/evaluate", json=prompt)
    assert first.status_code == 200
    assert first.json() == second.json()
    status = client.get("/api/v1/baseline")
    assert status.json()["session_count"] == 1


def test_empty_baseline_halts(client: TestClient) -> None:
    response = client.post(
        "/api/v1/evaluate",
        json={"prompt": "Add 20 lbs to Bench tomorrow."},
    )
    assert response.status_code == 200
    assert response.json()["halted"]["reason"] == "missing_baseline"


def test_qualitative_note_does_not_change_volume(client: TestClient) -> None:
    _put(client)
    response = client.post(
        "/api/v1/evaluate",
        json={"prompt": "I want to add 20 lbs to my bench press tomorrow"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["factors"]["volume_jump_pct"] == 10.8
    assert any(flag["kind"] == "qualitative_note" for flag in body["warnings"])


def test_embedding_nickname_scores_like_bench(
    client: TestClient, postgres_url: str
) -> None:
    import asyncio
    import json
    from pathlib import Path

    from overdone.db import create_engine, create_session_factory
    from overdone.ingest.catalog import seed_catalog

    mini = Path(__file__).resolve().parent / "fixtures" / "exercises_mini.json"

    async def seed() -> None:
        engine = create_engine(postgres_url)
        factory = create_session_factory(engine)
        async with factory() as session:
            await seed_catalog(session, json.loads(mini.read_text()))
            await session.commit()
        await engine.dispose()

    asyncio.run(seed())
    _put(client)
    response = client.post(
        "/api/v1/evaluate",
        json={"prompt": "Add 20 lbs to medium grip barbell bench tomorrow."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["halted"] is None
    assert body["overall_light"] == "yellow"
    assert body["items"][0]["factors"]["volume_jump_pct"] == 10.8
