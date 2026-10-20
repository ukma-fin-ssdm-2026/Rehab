
import pytest
from fastapi.testclient import TestClient

from backend.app import stubs
from backend.app.main import app

client = TestClient(app)
API_URL = "/api/v1/goals"
AUTH_HEADERS = {"Authorization": "Bearer user-42"}


@pytest.fixture(autouse=True)
def reset_test_data():
    stubs.reset()
    yield
    stubs.reset()


def test_get_existing_goal():
    response = client.get(f"{API_URL}/1", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json()["target_days"] == 30


def test_get_missing_goal():
    response = client.get(f"{API_URL}/999", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_get_other_users_goal():
    response = client.get(
        f"{API_URL}/1",
        headers={"Authorization": "Bearer user-43"},
    )
    assert response.status_code == 404


def test_create_goal():
    response = client.post(
        API_URL, headers=AUTH_HEADERS, json={"target_days": 7}
    )
    assert response.status_code == 201
    assert response.json()["target_days"] == 7
    assert response.json()["is_achieved"] is False
    assert response.headers["location"].endswith("/2")


def test_create_goal_without_authorization():
    response = client.post(API_URL, json={"target_days": 7})
    assert response.status_code == 401


@pytest.mark.parametrize("days", [0, -1, 3651])
def test_create_goal_invalid_days(days):
    response = client.post(
        API_URL, headers=AUTH_HEADERS, json={"target_days": days}
    )
    assert response.status_code == 422


def test_replace_goal():
    response = client.put(
        f"{API_URL}/1",
        headers=AUTH_HEADERS,
        json={"target_days": 60},
    )
    assert response.status_code == 200
    assert response.json()["target_days"] == 60
    assert response.json()["is_achieved"] is False


def test_replace_other_users_goal():
    response = client.put(
        f"{API_URL}/1",
        headers={"Authorization": "Bearer user-43"},
        json={"target_days": 60},
    )
    assert response.status_code == 404


def test_delete_goal():
    response = client.delete(f"{API_URL}/1", headers=AUTH_HEADERS)
    assert response.status_code == 204
    assert client.get(f"{API_URL}/1", headers=AUTH_HEADERS).status_code == 404


def test_delete_missing_goal():
    response = client.delete(f"{API_URL}/999", headers=AUTH_HEADERS)
    assert response.status_code == 404
