# AI-GENERATED START
"""Тести /health і /ready: працюють без реальної БД."""

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from backend.app.main import app
from backend.app.security import _db_session


class BrokenSession:
    def execute(self, *args, **kwargs):
        raise OperationalError(
            "SELECT 1", {}, Exception("postgresql+psycopg://user:secret@host/db")
        )


class WorkingSession:
    def execute(self, *args, **kwargs):
        return None


def _client(session_class):
    app.dependency_overrides[_db_session] = lambda: session_class()
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.pop(_db_session, None)


def test_health_ok_without_database():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_ok_when_database_answers():
    response = _client(WorkingSession).get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_ready_returns_503_without_leaking_connection_string():
    response = _client(BrokenSession).get("/ready")

    assert response.status_code == 503
    assert response.json()["code"] == "DATABASE_UNAVAILABLE"
    assert "secret" not in response.text
    assert "postgresql" not in response.text


def test_cors_preflight_allows_put_and_delete():
    client = TestClient(app)
    for method in ("PUT", "DELETE"):
        response = client.options(
            "/api/v1/calendar/entries",
            headers={
                "Origin": "http://localhost:8081",
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "Authorization",
            },
        )

        assert response.status_code == 200
        assert method in response.headers["access-control-allow-methods"]


def test_main_app_registers_auth_routes():
    paths = client.get("/openapi.json").json()["paths"]

    for route in ("register", "login", "me", "logout"):
        assert f"/api/v1/auth/{route}" in paths


# AI-GENERATED END
