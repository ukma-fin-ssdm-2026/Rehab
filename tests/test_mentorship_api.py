"""Real PostgreSQL/JWT contracts for the independently mountable router."""

from concurrent.futures import ThreadPoolExecutor
from importlib import import_module, util
from threading import Barrier

from fastapi import HTTPException
import pytest
from sqlalchemy import event, text
from sqlalchemy.orm import Session

from backend.app.core.clock import today_local

BASE = "/api/v1/mentorships"


@pytest.fixture
def mentorship_api(authenticated_calendar):
    assert (
        util.find_spec("backend.app.routers.mentorship") is not None
    ), "Mentorship router is missing"
    module = import_module("backend.app.routers.mentorship")
    authenticated_calendar.app.include_router(module.router, prefix="/api/v1")
    return authenticated_calendar


def code(db, uid):
    return db.scalar(
        text("SELECT mentor_code FROM users WHERE user_id=:id"), {"id": uid}
    )


def third_user(db):
    uid = db.scalar(
        text(
            "INSERT INTO users(email,name,nickname,password_hash,tracking_start_date) "
            "VALUES ('third@example.test','Third','third','test-hash',CURRENT_DATE) RETURNING user_id"
        )
    )
    db.commit()
    return uid


def joined(client, accounts, db):
    (mentor, headers), (mentee, _) = accounts
    response = client.post(
        BASE, headers=headers, json={"code": code(db, mentee["user_id"])}
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/code"),
        ("get", "/my-mentor"),
        ("get", "/my-mentees"),
        ("post", ""),
        ("get", "/1"),
        ("delete", "/1"),
        ("get", "/1/calendar/entries"),
        ("get", "/1/statistics"),
    ],
)
def test_all_routes_require_real_auth(mentorship_api, method, path):
    response = getattr(mentorship_api, method)(BASE + path)
    assert response.status_code == 401


def test_private_code_and_normalized_idempotent_join(
    mentorship_api, registered_users, calendar_db
):
    (mentor, headers), (mentee, _) = registered_users
    mine = mentorship_api.get(BASE + "/code", headers=headers)
    assert mine.json() == {"code": code(calendar_db, mentor["user_id"])}
    target_code = code(calendar_db, mentee["user_id"])
    first = mentorship_api.post(
        BASE, headers=headers, json={"code": "  " + target_code.lower() + "  "}
    )
    assert first.status_code == 201
    body = first.json()
    assert set(body["mentee"]) == {"user_id", "nickname", "email"}
    assert body["mentee"]["user_id"] == mentee["user_id"]
    assert body["mentor"]["user_id"] == mentor["user_id"]
    assert body["status"] == "active"
    second = mentorship_api.post(BASE, headers=headers, json={"code": target_code})
    assert second.status_code == 200
    assert second.json()["relationship_id"] == body["relationship_id"]
    assert calendar_db.scalar(text("SELECT count(*) FROM mentorships")) == 1
    assert mentorship_api.get(BASE + "/my-mentor", headers=headers).json() == {
        "item": None
    }
    mentee_headers = registered_users[1][1]
    assert (
        mentorship_api.get(BASE + "/my-mentor", headers=mentee_headers).json()["item"][
            "relationship_id"
        ]
        == body["relationship_id"]
    )


def test_join_rejects_self_unknown_malformed_and_identity_override(
    mentorship_api, registered_users, calendar_db
):
    (mentor, headers), (mentee, _) = registered_users
    own = mentorship_api.post(
        BASE, headers=headers, json={"code": code(calendar_db, mentor["user_id"])}
    )
    assert own.status_code == 422
    assert own.json()["code"] == "SELF_MENTORSHIP_NOT_ALLOWED"
    unknown = mentorship_api.post(BASE, headers=headers, json={"code": "AAAAAAAAAAAA"})
    assert unknown.status_code == 404
    assert unknown.json()["code"] == "INVALID_MENTOR_CODE"
    assert (
        mentorship_api.post(BASE, headers=headers, json={"code": "wrong"}).status_code
        == 422
    )
    assert (
        mentorship_api.post(
            BASE,
            headers=headers,
            json={
                "code": code(calendar_db, mentee["user_id"]),
                "mentor_id": mentee["user_id"],
            },
        ).status_code
        == 422
    )


def test_admin_cannot_participate(mentorship_api, registered_users, calendar_db):
    (mentor, headers), (mentee, mentee_headers) = registered_users
    calendar_db.execute(
        text("UPDATE users SET role='admin' WHERE user_id=:id"),
        {"id": mentee["user_id"]},
    )
    calendar_db.commit()
    assert mentorship_api.get(BASE + "/code", headers=mentee_headers).status_code == 403
    target = mentorship_api.post(
        BASE, headers=headers, json={"code": code(calendar_db, mentee["user_id"])}
    )
    assert target.status_code == 404


@pytest.mark.parametrize("side", [0, 1])
def test_ending_is_permanent_for_pair_but_not_global(
    mentorship_api, registered_users, calendar_db, side
):
    row = joined(mentorship_api, registered_users, calendar_db)
    rid = row["relationship_id"]
    headers = registered_users[side][1]
    assert mentorship_api.delete(f"{BASE}/{rid}", headers=headers).status_code == 204
    assert mentorship_api.delete(f"{BASE}/{rid}", headers=headers).status_code == 204
    assert (
        mentorship_api.get(f"{BASE}/{rid}", headers=headers).json()["status"] == "ended"
    )
    retry = mentorship_api.post(
        BASE,
        headers=registered_users[0][1],
        json={"code": code(calendar_db, registered_users[1][0]["user_id"])},
    )
    assert retry.status_code == 403
    assert retry.json()["code"] == "MENTORSHIP_REJOIN_FORBIDDEN"
    assert (
        mentorship_api.get(BASE + "/my-mentees", headers=registered_users[0][1]).json()[
            "total"
        ]
        == 0
    )
    other = third_user(calendar_db)
    from backend.app.security import create_access_token

    other_headers = {"Authorization": "Bearer " + create_access_token(other, 0)}
    assert (
        mentorship_api.post(
            BASE,
            headers=other_headers,
            json={"code": code(calendar_db, registered_users[1][0]["user_id"])},
        ).status_code
        == 201
    )


def test_lists_are_paged_and_roles_can_coexist(
    mentorship_api, registered_users, calendar_db
):
    row = joined(mentorship_api, registered_users, calendar_db)
    third = third_user(calendar_db)
    headers = registered_users[0][1]
    assert (
        mentorship_api.post(
            BASE, headers=headers, json={"code": code(calendar_db, third)}
        ).status_code
        == 201
    )
    page = mentorship_api.get(
        BASE + "/my-mentees?limit=1&offset=1", headers=headers
    ).json()
    assert (page["total"], page["limit"], page["offset"], len(page["items"])) == (
        2,
        1,
        1,
        1,
    )
    assert page["items"][0]["relationship_id"] == row["relationship_id"]
    # The reverse direction is separate and does not grant any automatic access.
    reverse = mentorship_api.post(
        BASE,
        headers=registered_users[1][1],
        json={"code": code(calendar_db, registered_users[0][0]["user_id"])},
    )
    assert reverse.status_code == 201
    assert (
        mentorship_api.get(BASE + "/my-mentor", headers=headers).json()["item"][
            "mentor"
        ]["user_id"]
        == registered_users[1][0]["user_id"]
    )


def test_read_only_calendar_statistics_and_foreign_record_isolation(
    mentorship_api, registered_users, calendar_db
):
    row = joined(mentorship_api, registered_users, calendar_db)
    (mentor, headers), (mentee, mentee_headers) = registered_users
    today = today_local().isoformat()
    calendar_db.execute(
        text(
            "UPDATE users SET tracking_start_date=CURRENT_DATE-10,best_streak=777 WHERE user_id=:id"
        ),
        {"id": mentee["user_id"]},
    )
    record = calendar_db.scalar(
        text(
            "INSERT INTO day_records(user_id,date,status,comment) VALUES (:id,CURRENT_DATE-2,'relapse','old note') RETURNING record_id"
        ),
        {"id": mentee["user_id"]},
    )
    foreign_record = calendar_db.scalar(
        text(
            "INSERT INTO day_records(user_id,date,status) VALUES (:id,CURRENT_DATE,'sober') RETURNING record_id"
        ),
        {"id": mentor["user_id"]},
    )
    calendar_db.commit()
    root = f"{BASE}/{row['relationship_id']}"
    page = mentorship_api.get(
        root + "/calendar/entries?limit=1&offset=0", headers=headers
    )
    assert page.status_code == 200
    assert page.json()["total"] == 1
    assert page.json()["items"][0]["comment"] == "old note"
    detail = mentorship_api.get(f"{root}/calendar/entries/{record}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["user_id"] == mentee["user_id"]
    assert (
        mentorship_api.get(
            f"{root}/calendar/entries/{foreign_record}", headers=headers
        ).status_code
        == 404
    )
    assert (
        mentorship_api.patch(
            f"{root}/calendar/entries/{record}",
            headers=headers,
            json={"status": "sober"},
        ).status_code
        == 405
    )
    assert (
        mentorship_api.patch(
            f"/api/v1/calendar/entries/{record}",
            headers=headers,
            json={"status": "sober"},
        ).status_code
        == 404
    )
    stats = mentorship_api.get(root + "/statistics?period=all", headers=headers)
    assert stats.status_code == 200
    assert stats.json()["period_end"] == today
    assert stats.json()["relapse_days"] == 1
    assert (
        calendar_db.scalar(
            text("SELECT best_streak FROM users WHERE user_id=:id"),
            {"id": mentee["user_id"]},
        )
        == 777
    )
    for suffix in ("/calendar/entries", "/statistics"):
        assert (
            mentorship_api.get(root + suffix, headers=mentee_headers).status_code == 404
        )
    assert (
        mentorship_api.get(
            root + "/calendar/entries?from=2026-02-02&to=2026-01-01", headers=headers
        ).status_code
        == 422
    )
    assert mentorship_api.delete(root, headers=mentee_headers).status_code == 204
    for suffix in ("/calendar/entries", f"/calendar/entries/{record}", "/statistics"):
        assert mentorship_api.get(root + suffix, headers=headers).status_code == 403


def test_outsider_cannot_inspect_or_end_relationship(
    mentorship_api, registered_users, calendar_db
):
    row = joined(mentorship_api, registered_users, calendar_db)
    third = third_user(calendar_db)
    from backend.app.security import create_access_token

    headers = {"Authorization": "Bearer " + create_access_token(third, 0)}
    root = f"{BASE}/{row['relationship_id']}"
    for method, suffix in (
        ("get", ""),
        ("delete", ""),
        ("get", "/statistics"),
        ("get", "/calendar/entries"),
    ):
        assert (
            getattr(mentorship_api, method)(root + suffix, headers=headers).status_code
            == 404
        )


def test_competing_mentors_are_serialized(postgres_schema, calendar_db, db_users):
    first, mentee = db_users
    third = third_user(calendar_db)
    target = code(calendar_db, mentee)
    calendar_db.commit()
    service = import_module("backend.app.services.mentorship")
    assert hasattr(service, "join_by_code"), "Joining service is missing"
    barrier = Barrier(2)

    def join(actor):
        with Session(postgres_schema) as session:
            session.execute(text("SET LOCAL lock_timeout='3s'"))
            barrier.wait(timeout=5)
            try:
                _, created = service.join_by_code(session, actor, target)
                session.commit()
                return 201 if created else 200
            except HTTPException as error:
                session.rollback()
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(join, actor) for actor in (first, third)]
        assert sorted(f.result(timeout=10) for f in futures) == [201, 409]
    assert (
        calendar_db.scalar(
            text("SELECT count(*) FROM mentorships WHERE status='active'")
        )
        == 1
    )


def test_reciprocal_joins_do_not_deadlock(postgres_schema, calendar_db, db_users):
    first, second = db_users
    targets = {first: code(calendar_db, second), second: code(calendar_db, first)}
    calendar_db.commit()
    service = import_module("backend.app.services.mentorship")
    barrier = Barrier(2)

    def synchronize_inserts(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("INSERT INTO MENTORSHIPS"):
            barrier.wait(timeout=5)

    def join(actor):
        with Session(postgres_schema) as session:
            session.execute(text("SET LOCAL lock_timeout='3s'"))
            _, created = service.join_by_code(session, actor, targets[actor])
            session.commit()
            return created

    event.listen(postgres_schema, "before_cursor_execute", synchronize_inserts)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(join, actor) for actor in (first, second)]
            assert all(f.result(timeout=10) for f in futures)
    finally:
        event.remove(postgres_schema, "before_cursor_execute", synchronize_inserts)
    assert calendar_db.scalar(text("SELECT count(*) FROM mentorships")) == 2


def test_join_service_does_not_commit_callers_transaction(calendar_db, db_users):
    service = import_module("backend.app.services.mentorship")
    first, second = db_users
    _, created = service.join_by_code(calendar_db, first, code(calendar_db, second))
    assert created
    calendar_db.rollback()
    assert calendar_db.scalar(text("SELECT count(*) FROM mentorships")) == 0
