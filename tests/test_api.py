from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_openapi_available():
    response = client.get("/openapi.json")

    assert response.status_code == 200


def test_calendar_route_exists():
    response = client.get("/openapi.json")
    routes = response.json()["paths"]

    assert "/api/v1/calendar/entries" in routes


def test_goals_route_exists():
    response = client.get("/openapi.json")
    routes = response.json()["paths"]

    assert "/api/v1/goals" in routes