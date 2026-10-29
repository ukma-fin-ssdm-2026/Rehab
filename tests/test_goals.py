"""API-тести фіксованих етапів тверезості на PostgreSQL."""

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from backend.app.core.clock import today_local
from backend.app.db.models.entry import DayRecord
from backend.app.db.models.goal import Goal
from backend.app.db.models.user import User
from backend.app.main import app
from backend.app.security import CurrentUser, _db_session, get_current_user

client = TestClient(app)
API_URL = "/api/v1/goals"


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
        )
    )
    calendar_db.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(owner_id, "user")
    app.dependency_overrides[_db_session] = lambda: calendar_db
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(_db_session, None)


def test_list_returns_fixed_milestones_without_user_goal_rows(calendar_db, db_users):
    response = client.get(API_URL)

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"target_days": 7, "is_achieved": False, "progress_days": 1},
            {"target_days": 30, "is_achieved": False, "progress_days": 1},
        ]
    }
    assert calendar_db.query(Goal).filter_by(user_id=db_users[0]).count() == 0


def test_legacy_personal_goal_rows_do_not_change_fixed_milestones(calendar_db, db_users):
    calendar_db.add(
        Goal(user_id=db_users[0], target_days=10, is_achieved=False)
    )
    calendar_db.commit()

    response = client.get(API_URL)

    assert response.status_code == 200
    assert [item["target_days"] for item in response.json()["items"]] == [7, 30]


def test_goal_collection_requires_authentication(calendar_db):
    app.dependency_overrides.pop(get_current_user, None)
    response = client.get(API_URL)
    assert response.status_code == 401


def test_goal_collection_is_read_only():
    assert client.post(API_URL, json={"target_days": 10}).status_code == 405
    assert client.put(f"{API_URL}/7", json={"target_days": 10}).status_code == 404
    assert client.delete(f"{API_URL}/7").status_code == 404
    assert client.get(f"{API_URL}/7").status_code == 404
