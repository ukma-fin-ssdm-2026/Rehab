import pytest

API_URL = "/api/v1/goals"


def test_get_existing_goal(prototype_api):
    data = prototype_api
    response = data.client.get(f"{API_URL}/1", headers=data.headers)
    assert response.status_code == 200
    assert response.json()["target_days"] == 30


def test_get_missing_goal(prototype_api):
    data = prototype_api
    response = data.client.get(f"{API_URL}/999", headers=data.headers)
    assert response.status_code == 404


def test_get_other_users_goal(prototype_api):
    data = prototype_api
    response = data.client.get(
        f"{API_URL}/1",
        headers=data.other_headers,
    )
    assert response.status_code == 404


def test_create_goal(prototype_api):
    data = prototype_api
    response = data.client.post(API_URL, headers=data.headers, json={"target_days": 7})
    assert response.status_code == 201
    assert response.json()["target_days"] == 7
    assert response.json()["is_achieved"] is False
    assert response.headers["location"].endswith("/2")


def test_create_goal_without_authorization(prototype_api):
    data = prototype_api
    response = data.client.post(API_URL, json={"target_days": 7})
    assert response.status_code == 401


@pytest.mark.parametrize("days", [0, -1, 3651])
def test_create_goal_invalid_days(days, prototype_api):
    data = prototype_api
    response = data.client.post(
        API_URL, headers=data.headers, json={"target_days": days}
    )
    assert response.status_code == 422


def test_replace_goal(prototype_api):
    data = prototype_api
    response = data.client.put(
        f"{API_URL}/1",
        headers=data.headers,
        json={"target_days": 60},
    )
    assert response.status_code == 200
    assert response.json()["target_days"] == 60
    assert response.json()["is_achieved"] is False


def test_replace_other_users_goal(prototype_api):
    data = prototype_api
    response = data.client.put(
        f"{API_URL}/1",
        headers=data.other_headers,
        json={"target_days": 60},
    )
    assert response.status_code == 404


def test_delete_goal(prototype_api):
    data = prototype_api
    response = data.client.delete(f"{API_URL}/1", headers=data.headers)
    assert response.status_code == 204
    assert data.client.get(f"{API_URL}/1", headers=data.headers).status_code == 404


def test_delete_missing_goal(prototype_api):
    data = prototype_api
    response = data.client.delete(f"{API_URL}/999", headers=data.headers)
    assert response.status_code == 404
