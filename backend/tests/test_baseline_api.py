import json
from pathlib import Path

from fastapi.testclient import TestClient

SAMPLE_JSON = Path(__file__).resolve().parents[2] / "data" / "sample_baseline.json"
SAMPLE_TEXT = Path(__file__).resolve().parents[2] / "data" / "sample_baseline.txt"


def test_put_sample_baseline_round_trips_session_notes(client: TestClient) -> None:
    payload = json.loads(SAMPLE_JSON.read_text())
    response = client.put("/api/v1/baseline", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["session_count"] == 1
    assert body["benchmark_count"] == 1
    assert (
        body["baseline"]["sessions"][0]["notes"] == "Right shoulder felt tight on set 3"
    )

    fetched = client.get("/api/v1/baseline")
    assert fetched.status_code == 200
    assert fetched.json()["baseline"]["sessions"][0]["notes"] == (
        "Right shoulder felt tight on set 3"
    )


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
    assert body["session_count"] == 1
    assert body["benchmark_count"] == 1
    assert (
        body["baseline"]["sessions"][0]["notes"] == "Right shoulder felt tight on set 3"
    )
    assert body["baseline"]["sessions"][0]["sets"][0]["exercise"] == (
        "Barbell Bench Press - Medium Grip"
    )
    assert body["baseline"]["sessions"][0]["sets"][0]["sets"] == 4
    assert body["baseline"]["sessions"][0]["sets"][0]["reps"] == 5


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
