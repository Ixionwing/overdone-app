import json
from pathlib import Path

from fastapi.testclient import TestClient

SAMPLE_JSON = Path(__file__).resolve().parents[2] / "data" / "sample_baseline.json"
SAMPLE_TEXT = Path(__file__).resolve().parents[2] / "data" / "sample_baseline.txt"


def _shoulder_session(sessions: list[dict]) -> dict:
    return next(
        session
        for session in sessions
        if (session.get("notes") or "").find("shoulder felt tight") >= 0
    )


def _set(session: dict, exercise: str) -> dict:
    return next(item for item in session["sets"] if item["exercise"] == exercise)


def test_put_sample_baseline_round_trips_session_notes(client: TestClient) -> None:
    payload = json.loads(SAMPLE_JSON.read_text())
    response = client.put("/api/v1/baseline", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["session_count"] == 12
    assert body["benchmark_count"] == 4
    sessions = body["baseline"]["sessions"]
    assert sessions[0]["date"] == "2026-09-07"
    assert sessions[-1]["date"] == "2026-09-19"
    assert _shoulder_session(sessions)["notes"] == "Right shoulder felt tight on set 3"

    fetched = client.get("/api/v1/baseline")
    assert fetched.status_code == 200
    assert (
        _shoulder_session(fetched.json()["baseline"]["sessions"])["notes"]
        == "Right shoulder felt tight on set 3"
    )


def test_sample_baseline_progresses_ppl_compounds_across_two_weeks(
    client: TestClient,
) -> None:
    payload = json.loads(SAMPLE_JSON.read_text())
    sessions = {row["date"]: row for row in payload["sessions"]}
    assert (
        _set(sessions["2026-09-07"], "Barbell Bench Press - Medium Grip")["weight"]
        == 185
    )
    assert (
        _set(sessions["2026-09-14"], "Barbell Bench Press - Medium Grip")["weight"]
        == 190
    )
    assert _set(sessions["2026-09-09"], "Barbell Squat")["weight"] == 225
    assert _set(sessions["2026-09-16"], "Barbell Squat")["weight"] == 230
    assert _set(sessions["2026-09-08"], "Barbell Deadlift")["weight"] == 275
    assert _set(sessions["2026-09-15"], "Barbell Deadlift")["weight"] == 285
    assert _set(sessions["2026-09-10"], "Standing Military Press")["weight"] == 95
    assert _set(sessions["2026-09-17"], "Standing Military Press")["weight"] == 100

    response = client.put("/api/v1/baseline", json=payload)
    assert response.status_code == 200
    assert response.json()["session_count"] == 12


def test_second_put_replaces_rather_than_appends(client: TestClient) -> None:
    payload = json.loads(SAMPLE_JSON.read_text())
    client.put("/api/v1/baseline", json=payload)
    replacement = {
        "preferred_unit": "lb",
        "benchmarks": [],
        "sessions": [
            {
                "date": "2026-09-14",
                "notes": "only this session",
                "sets": [
                    {
                        "exercise": "Squat",
                        "weight": 135,
                        "unit": "lb",
                        "reps": 5,
                        "sets": 3,
                    }
                ],
            }
        ],
    }
    response = client.put("/api/v1/baseline", json=replacement)
    assert response.status_code == 200
    body = response.json()
    assert body["session_count"] == 1
    assert body["benchmark_count"] == 0
    assert body["baseline"]["sessions"][0]["notes"] == "only this session"


def test_get_empty_baseline_is_empty_lists(client: TestClient) -> None:
    response = client.get("/api/v1/baseline")
    assert response.status_code == 200
    body = response.json()
    assert body["session_count"] == 0
    assert body["benchmark_count"] == 0
    assert body["baseline"]["sessions"] == []
    assert body["baseline"]["benchmarks"] == []


def test_post_text_baseline_matches_sample_json(client: TestClient) -> None:
    response = client.post(
        "/api/v1/baseline/text", json={"text": SAMPLE_TEXT.read_text()}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["session_count"] == 12
    assert body["benchmark_count"] == 4
    sessions = body["baseline"]["sessions"]
    assert _shoulder_session(sessions)["notes"] == "Right shoulder felt tight on set 3"
    first = sessions[0]["sets"][0]
    assert first["exercise"] == "Barbell Bench Press - Medium Grip"
    assert first["sets"] == 4
    assert first["reps"] == 5
    assert first["weight"] == 185
    json_body = client.put(
        "/api/v1/baseline", json=json.loads(SAMPLE_JSON.read_text())
    ).json()
    assert json_body["baseline"]["sessions"] == body["baseline"]["sessions"]
    assert json_body["baseline"]["benchmarks"] == body["baseline"]["benchmarks"]


def test_put_binds_catalog_exercise_id_on_sets_and_benchmarks(
    client: TestClient,
) -> None:
    payload = json.loads(SAMPLE_JSON.read_text())
    response = client.put("/api/v1/baseline", json=payload)
    assert response.status_code == 200
    body = response.json()
    set_id = body["baseline"]["sessions"][0]["sets"][0]["exercise_id"]
    bench_id = body["baseline"]["benchmarks"][0]["exercise_id"]
    assert set_id is not None
    assert bench_id == set_id
    fetched = client.get("/api/v1/baseline")
    assert fetched.json()["baseline"]["sessions"][0]["sets"][0]["exercise_id"] == set_id
    replay = client.put("/api/v1/baseline", json=fetched.json()["baseline"])
    assert replay.status_code == 200
    assert replay.json()["baseline"]["sessions"][0]["sets"][0]["exercise_id"] == set_id


def test_put_leaves_exercise_id_null_when_catalog_misses(client: TestClient) -> None:
    response = client.put(
        "/api/v1/baseline",
        json={
            "preferred_unit": "lb",
            "benchmarks": [],
            "sessions": [
                {
                    "date": "2026-09-14",
                    "notes": None,
                    "sets": [
                        {
                            "exercise": "zzzxnotanexercise999",
                            "weight": 100,
                            "unit": "lb",
                            "reps": 5,
                            "sets": 1,
                        }
                    ],
                }
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["baseline"]["sessions"][0]["sets"][0]["exercise_id"] is None
