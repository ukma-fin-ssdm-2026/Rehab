"""API-тести особистих цілей на PostgreSQL."""

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from backend.app.core.clock import today_local, utc_now
from backend.app.db.models.entry import DayRecord
from backend.app.db.models.user import User
from backend.app.main import app
from backend.app.repositories.goals import create_goal as add_goal
from backend.app.security import CurrentUser, _db_session, get_current_user

client = TestClient(app)
API_URL = "/api/v1/goals"
AUTH_HEADERS = {"Authorization": "Bearer integration-test"}


@pytest.fixture(autouse=True)
def reset_test_data(calendar_db, db_users):
    owner_id, _ = db_users
    today = today_local()
    account = calendar_db.get(User, owner_id)
    account.tracking_start_date = today - dt.timedelta(days=6)
    calendar_db.add(
        DayRecord(
            user_id=owner_id,
            date=today - dt.timedelta(days=1),
            status="relapse",
            trigger_category="stress",
            drinks=[],
            created_at=utc_now(),
        )
    )
    add_goal(calendar_db, owner_id, 30)
    calendar_db.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(owner_id, "user")
    app.dependency_overrides[_db_session] = lambda: calendar_db
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(_db_session, None)


def test_get_existing_goal():
    response = client.get(f"{API_URL}/1", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json()["target_days"] == 30
    assert response.json()["progress_days"] == 1
    assert response.json()["is_achieved"] is False
    assert "created_at" in response.json()


def test_get_missing_goal():
    response = client.get(f"{API_URL}/999", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_get_other_users_goal(db_users):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(db_users[1], "user")
    response = client.get(
        f"{API_URL}/1",
        headers={"Authorization": "Bearer other-integration-test"},
    )
    assert response.status_code == 404


def test_create_goal(db_users):
    response = client.post(API_URL, headers=AUTH_HEADERS, json={"target_days": 7})
    assert response.status_code == 201
    assert response.json()["target_days"] == 7
    assert response.json()["is_achieved"] is False
    assert response.json()["progress_days"] == 1
    assert response.headers["location"].endswith("/2")


def test_create_goal_checks_existing_history():
    response = client.post(
        API_URL,
        headers=AUTH_HEADERS,
        json={"target_days": 1},
    )

    assert response.status_code == 201
    assert response.json()["is_achieved"] is True
    assert response.json()["progress_days"] == 1


@pytest.mark.parametrize("days", [0, -1, 3651, True, 10.5, "10"])
def test_create_goal_invalid_days(days):
    response = client.post(API_URL, headers=AUTH_HEADERS, json={"target_days": days})
    assert response.status_code == 422


@pytest.mark.parametrize("field", ["user_id", "is_achieved"])
def test_create_goal_rejects_server_owned_fields(field):
    response = client.post(
        API_URL,
        headers=AUTH_HEADERS,
        json={"target_days": 10, field: 42},
    )

    assert response.status_code == 422


def test_list_goals_filters_user_and_paginates(calendar_db, db_users):
    add_goal(calendar_db, db_users[0], 10)
    add_goal(calendar_db, db_users[1], 20)
    calendar_db.commit()

    first_page = client.get(API_URL, headers=AUTH_HEADERS, params={"limit": 1})
    second_page = client.get(
        API_URL,
        headers=AUTH_HEADERS,
        params={"limit": 1, "offset": 1},
    )

    assert first_page.status_code == 200
    assert first_page.json() == {
        "items": [first_page.json()["items"][0]],
        "total": 2,
        "limit": 1,
        "offset": 0,
    }
    assert first_page.json()["items"][0]["goal_id"] == 1
    assert second_page.status_code == 200
    assert second_page.json()["items"][0]["goal_id"] == 2
    assert second_page.json()["total"] == 2


@pytest.mark.parametrize("params", [{"limit": 0}, {"offset": -1}])
def test_list_goals_rejects_invalid_pagination(params):
    response = client.get(API_URL, headers=AUTH_HEADERS, params=params)

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


def test_replace_other_users_goal(db_users):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(db_users[1], "user")
    response = client.put(
        f"{API_URL}/1",
        headers={"Authorization": "Bearer other-integration-test"},
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
