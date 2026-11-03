"""PostgreSQL HTTP contracts before the team switches the production router.

Only the authentication and progress boundaries use explicit test doubles.
Requests, schema, SQL, constraints and transactions are real.
"""

import datetime as dt
import importlib

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.clock import today_local
from backend.app.db.session import get_db
from backend.app.errors import api_error
from backend.app.main import http_exception_handler, validation_exception_handler
from backend.app.security import CurrentUser, get_current_user

URL = "/api/v1/calendar/entries"
HEADERS = {"Authorization": "Bearer test-first"}


@pytest.fixture
def calendar_api(postgres_schema, db_users):
    module = importlib.import_module("backend.app.routers.calendar_postgres")
    application = FastAPI()
    application.add_exception_handler(HTTPException, http_exception_handler)
    application.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )
    application.include_router(module.router, prefix="/api/v1")

    def current(request: Request):
        header = request.headers.get("Authorization")
        users = {"Bearer test-first": db_users[0], "Bearer test-second": db_users[1]}
        if header not in users:
            raise api_error(401, "UNAUTHORIZED", "Test session required")
        return CurrentUser(users[header], "user")

    def database():
        with Session(postgres_schema, expire_on_commit=False) as db:
            try:
                yield db
            except BaseException:
                db.rollback()
                raise

    calls = []

    def progress(db, user_id, today):
        calls.append((user_id, today))

    application.dependency_overrides[get_current_user] = current
    application.dependency_overrides[get_db] = database
    application.dependency_overrides[module.get_progress_sync] = lambda: progress
    with TestClient(application, raise_server_exceptions=False) as client:
        yield client, application, module, calls


def payload(**changes):
    return {"date": str(today_local()), "status": "sober", **changes}


def test_create_list_details_and_progress_callback(calendar_api, db_users):
    client, _, _, calls = calendar_api
    response = client.post(URL, headers=HEADERS, json=payload())
    assert response.status_code == 201
    record_id = response.json()["record_id"]
    assert response.headers["Location"].endswith(f"/{record_id}")
    assert client.get(f"{URL}/{record_id}", headers=HEADERS).json() == response.json()
    listing = client.get(URL, headers=HEADERS).json()
    assert listing["total"] == 1
    assert len(listing["items"]) == 1
    assert calls == [(db_users[0], today_local())]


def test_duplicate_is_409_and_does_not_remove_original(calendar_api):
    client, _, _, calls = calendar_api
    assert client.post(URL, headers=HEADERS, json=payload()).status_code == 201
    response = client.post(URL, headers=HEADERS, json=payload())
    assert response.status_code == 409
    assert response.json()["code"] == "ENTRY_ALREADY_EXISTS"
    assert client.get(URL, headers=HEADERS).json()["total"] == 1
    assert len(calls) == 1


def test_missing_session_and_other_user_are_rejected(calendar_api):
    client, _, _, _ = calendar_api
    assert client.get(URL).status_code == 401
    record_id = client.post(URL, headers=HEADERS, json=payload()).json()["record_id"]
    second = {"Authorization": "Bearer test-second"}
    assert client.get(URL, headers=second).json()["total"] == 0
    assert client.get(f"{URL}/{record_id}", headers=second).status_code == 404
    assert (
        client.patch(
            f"{URL}/{record_id}", headers=second, json={"status": "relapse"}
        ).status_code
        == 404
    )


def test_failed_progress_rolls_back_entry_and_derived_writes(
    calendar_api, calendar_db, db_users
):
    client, application, module, _ = calendar_api

    def failing(db, user_id, today):
        db.execute(
            text("UPDATE users SET best_streak=99 WHERE user_id=:id"), {"id": user_id}
        )
        raise RuntimeError("Simulated statistics failure")

    application.dependency_overrides[module.get_progress_sync] = lambda: failing
    assert client.post(URL, headers=HEADERS, json=payload()).status_code == 500
    assert calendar_db.scalar(text("SELECT count(*) FROM day_records")) == 0
    assert (
        calendar_db.scalar(
            text("SELECT best_streak FROM users WHERE user_id=:id"), {"id": db_users[0]}
        )
        == 0
    )


def test_unintegrated_progress_fails_closed_without_partial_write(
    calendar_api, calendar_db, monkeypatch
):
    client, application, module, _ = calendar_api
    del application.dependency_overrides[module.get_progress_sync]

    def missing(name):
        raise ModuleNotFoundError(name=name)

    monkeypatch.setattr(module, "import_module", missing)
    response = client.post(URL, headers=HEADERS, json=payload())
    assert response.status_code == 503
    assert response.json()["code"] == "PROGRESS_SYNC_UNAVAILABLE"
    assert calendar_db.scalar(text("SELECT count(*) FROM day_records")) == 0


def test_old_entry_patch_returns_domain_error(calendar_api, calendar_db):
    client, _, _, _ = calendar_api
    record_id = client.post(URL, headers=HEADERS, json=payload()).json()["record_id"]
    calendar_db.execute(
        text("UPDATE day_records SET created_at=:old WHERE record_id=:id"),
        {
            "old": dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=49),
            "id": record_id,
        },
    )
    calendar_db.commit()
    response = client.patch(
        f"{URL}/{record_id}", headers=HEADERS, json={"status": "relapse"}
    )
    assert response.status_code == 403
    assert response.json()["code"] == "EDIT_WINDOW_EXPIRED"


def test_invalid_date_interval_and_body_return_structured_422(calendar_api):
    client, _, _, _ = calendar_api
    response = client.get(
        URL, headers=HEADERS, params={"from": "2026-10-29", "to": "2026-10-28"}
    )
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_DATE_RANGE"
    response = client.post(URL, headers=HEADERS, json=payload(user_id=999))
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_recent_patch_updates_details_and_progress(calendar_api):
    client, _, _, calls = calendar_api
    created = client.post(
        URL,
        headers=HEADERS,
        json=payload(
            status="relapse",
            trigger_category="stress",
            drinks=[{"type": "beer", "volume_ml": 330}],
        ),
    )
    record_id = created.json()["record_id"]
    response = client.patch(
        f"{URL}/{record_id}", headers=HEADERS, json={"status": "sober"}
    )
    assert response.status_code == 200
    assert response.json()["created_at"] == created.json()["created_at"]
    assert response.json()["drinks"] == []
    assert response.json()["trigger_category"] is None
    assert len(calls) == 2
