from fastapi.testclient import TestClient

from overdone.config import Settings
from overdone.main import create_app


def test_health_ok(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_returns_503_when_database_unreachable():
    settings = Settings(
        database_url="postgresql+asyncpg://overdone:overdone@127.0.0.1:1/overdone"
    )
    with TestClient(create_app(settings)) as test_client:
        response = test_client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"detail": "database unavailable"}
