import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastmcp import Client
from tests.test_evaluate_api import RICH, _put


def _call_mcp(client: TestClient, name: str, arguments: dict) -> dict:
    app = client.app
    assert isinstance(app, FastAPI)
    portal = client.portal
    assert portal is not None

    async def run() -> dict:
        async with Client(app.state.mcp) as mcp_client:
            result = await mcp_client.call_tool(name, arguments)
            return result.structured_content or {}

    return portal.call(run)


def test_evaluate_prompt_tool_returns_light(client: TestClient) -> None:
    _put(client)
    body = _call_mcp(
        client,
        "evaluate_prompt",
        {"prompt": "I want to add 20 lbs to my bench press tomorrow"},
    )
    assert body["halted"] is None
    assert body["overall_light"] == "yellow"
    assert body["items"][0]["factors"]["volume_jump_pct"] == 10.8


def test_mcp_evaluate_matches_http(client: TestClient) -> None:
    _put(client)
    prompt = {"prompt": "Reach a 225 lb Squat by next month."}
    http_body = client.post("/api/v1/evaluate", json=prompt).json()
    assert _call_mcp(client, "evaluate_prompt", prompt) == http_body


def test_replace_baseline_json_tool(client: TestClient) -> None:
    body = _call_mcp(
        client,
        "replace_baseline_json",
        {"payload": json.dumps(RICH)},
    )
    assert body["session_count"] == 1
    fetched = client.get("/api/v1/baseline").json()
    assert fetched["session_count"] == 1
