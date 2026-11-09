import requests
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from backend.app.routers import health
from backend.app.security import _db_session


class WorkingDatabase:
    def execute(self, statement):
        assert str(statement) == "SELECT 1"


class BrokenDatabase:
    def execute(self, statement):
        raise OperationalError(
            "SELECT 1", {}, Exception("postgresql://secret-password@host/database")
        )


class GmailResponse:
    def __init__(self, payload=None, error=None):
        self.payload = (
            {"name": "gmail", "version": "v1"} if payload is None else payload
        )
        self.error = error

    def raise_for_status(self):
        if self.error is not None:
            raise self.error

    def json(self):
        return self.payload


def client_for(database):
    app = FastAPI()
    app.include_router(health.router)
    app.dependency_overrides[_db_session] = lambda: database
    return TestClient(app)


def test_bonus2_all_dependencies_healthy(monkeypatch):
    observed = []

    def gmail_get(url, timeout):
        observed.append((url, timeout))
        return GmailResponse()

    monkeypatch.setattr(health.requests, "get", gmail_get)

    response = client_for(WorkingDatabase()).get("/health/dependencies")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "dependencies": {"database": "ok", "gmail_api": "ok"},
    }
    assert observed == [(health.GMAIL_DISCOVERY_URL, 3)]


def test_bonus2_broken_database_returns_unhealthy(monkeypatch):
    monkeypatch.setattr(health.requests, "get", lambda *args, **kwargs: GmailResponse())

    response = client_for(BrokenDatabase()).get("/health/dependencies")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unhealthy",
        "dependencies": {"database": "unhealthy", "gmail_api": "ok"},
    }
    assert "secret-password" not in response.text
    assert "postgresql" not in response.text


def test_bonus2_gmail_timeout_returns_unhealthy(monkeypatch):
    def gmail_timeout(url, timeout):
        assert timeout == 3
        raise requests.Timeout("internal-api-secret")

    monkeypatch.setattr(health.requests, "get", gmail_timeout)

    response = client_for(WorkingDatabase()).get("/health/dependencies")

    assert response.status_code == 503
    assert response.json()["dependencies"] == {
        "database": "ok",
        "gmail_api": "unhealthy",
    }
    assert "internal-api-secret" not in response.text


def test_bonus2_gmail_http_error_returns_unhealthy(monkeypatch):
    monkeypatch.setattr(
        health.requests,
        "get",
        lambda *args, **kwargs: GmailResponse(
            error=requests.HTTPError("private-server-details")
        ),
    )

    response = client_for(WorkingDatabase()).get("/health/dependencies")

    assert response.status_code == 503
    assert response.json()["status"] == "unhealthy"
    assert response.json()["dependencies"]["gmail_api"] == "unhealthy"
    assert "private-server-details" not in response.text


def test_bonus2_invalid_gmail_discovery_returns_unhealthy(monkeypatch):
    monkeypatch.setattr(
        health.requests,
        "get",
        lambda *args, **kwargs: GmailResponse(
            payload={"name": "other", "version": "v1"}
        ),
    )

    response = client_for(WorkingDatabase()).get("/health/dependencies")

    assert response.status_code == 503
    assert response.json()["dependencies"]["gmail_api"] == "unhealthy"


def test_bonus2_both_dependencies_unhealthy(monkeypatch):
    def unavailable(url, timeout):
        raise requests.ConnectionError("connection-private-details")

    monkeypatch.setattr(health.requests, "get", unavailable)

    response = client_for(BrokenDatabase()).get("/health/dependencies")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unhealthy",
        "dependencies": {"database": "unhealthy", "gmail_api": "unhealthy"},
    }
    assert "connection-private-details" not in response.text


def test_bonus2_existing_health_and_readiness_unchanged(monkeypatch):
    def unavailable(url, timeout):
        raise requests.Timeout("not reachable")

    monkeypatch.setattr(health.requests, "get", unavailable)
    client = client_for(WorkingDatabase())

    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ok", "database": "ok"}
