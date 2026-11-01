"""Access helpers enforce active relationships using real SQL services."""

from importlib import import_module, util

from fastapi import HTTPException
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.repositories import users
from backend.app.db.models.user import User
from tests.test_full_schema import relationship


def services():
    assert (
        util.find_spec("backend.app.services.mentorship") is not None
    ), "Shared mentorship access service is not implemented"
    return import_module("backend.app.services.mentorship")


def test_code_collision_retries_without_losing_existing_transaction(
    calendar_db, monkeypatch
):
    calendar_db.add(
        User(
            name="Existing",
            nickname="existing",
            email="existing@example.test",
            password_hash="hash",
            tracking_start_date="2026-10-01",
            mentor_code="AAAAAAAAAAAA",
        )
    )
    calendar_db.flush()
    codes = iter(["AAAAAAAAAAAA", "BBBBBBBBBBBB"])
    monkeypatch.setattr(
        users, "generate_mentor_code", lambda: next(codes), raising=False
    )
    account = users.create_user(
        calendar_db,
        name="New",
        nickname="new",
        email="new@example.test",
        password_hash="hash",
        tracking_start_date="2026-10-01",
    )
    assert account.mentor_code == "BBBBBBBBBBBB"
    assert calendar_db.scalar(text("SELECT count(*) FROM users")) == 2


def test_only_active_mentor_can_read_mentee(calendar_db, db_users):
    service = services()
    mentor, mentee = db_users
    rid = relationship(calendar_db, mentor, mentee)
    assert service.require_active_mentor(calendar_db, mentor, rid).mentee_id == mentee
    assert (
        service.require_active_mentor(calendar_db, mentor, rid, lock=True).mentee_id
        == mentee
    )
    for actor in (mentee, 999):
        with pytest.raises(HTTPException) as error:
            service.require_active_mentor(calendar_db, actor, rid)
        assert error.value.status_code == 404
    with pytest.raises(HTTPException) as error:
        service.require_active_mentor(calendar_db, mentor, 999)
    assert error.value.status_code == 404


def test_cached_access_is_revoked_after_another_session_ends_relationship(
    calendar_db, db_users
):
    service = services()
    mentor, mentee = db_users
    rid = relationship(calendar_db, mentor, mentee)
    calendar_db.commit()
    cached = service.require_active_mentor(calendar_db, mentor, rid)
    assert cached.status == "active"
    with Session(calendar_db.get_bind()) as other:
        service.end_relationship(other, rid, mentee, "mentee_left")
        other.commit()
    with pytest.raises(HTTPException) as error:
        service.require_active_mentor(calendar_db, mentor, rid)
    assert error.value.status_code == 403
    assert error.value.detail["code"] == "MENTORSHIP_INACTIVE"


@pytest.mark.parametrize("side,reason", [(0, "mentor_left"), (1, "mentee_left")])
def test_end_revokes_access_preserves_history_and_does_not_commit(
    calendar_db, db_users, side, reason
):
    service = services()
    mentor, mentee = db_users
    rid = relationship(calendar_db, mentor, mentee)
    calendar_db.commit()
    row = service.end_relationship(calendar_db, rid, db_users[side], reason)
    assert row.status == "ended"
    assert row.ended_reason == reason
    assert row.ended_by == db_users[side]
    assert row.ended_at is not None
    assert (
        service.require_relationship_participant(calendar_db, mentee, rid).status
        == "ended"
    )
    with pytest.raises(HTTPException) as error:
        service.require_active_mentor(calendar_db, mentor, rid)
    assert error.value.status_code == 403
    assert error.value.detail["code"] == "MENTORSHIP_INACTIVE"
    service.end_relationship(calendar_db, rid, db_users[side], reason)
    calendar_db.rollback()
    assert service.require_active_mentor(calendar_db, mentor, rid).status == "active"


def test_end_rejects_outsider_and_client_complaint_reason(calendar_db, db_users):
    service = services()
    mentor, mentee = db_users
    rid = relationship(calendar_db, mentor, mentee)
    for actor, reason, expected in [
        (999, "mentor_left", 404),
        (mentor, "complaint", 403),
        (mentee, "mentor_left", 403),
    ]:
        with pytest.raises(HTTPException) as error:
            service.end_relationship(calendar_db, rid, actor, reason)
        assert error.value.status_code == expected
    assert service.require_active_mentor(calendar_db, mentor, rid).status == "active"


def test_only_admin_service_can_end_for_complaint(calendar_db, db_users):
    service = services()
    mentor, mentee = db_users
    rid = relationship(calendar_db, mentor, mentee)
    with pytest.raises(HTTPException) as error:
        service.end_relationship_for_complaint(calendar_db, rid, mentor)
    assert error.value.status_code == 403
    admin = calendar_db.scalar(
        text(
            "INSERT INTO users(email,name,nickname,password_hash,tracking_start_date,role) "
            "VALUES ('admin@example.test','Admin','admin','hash',CURRENT_DATE,'admin') RETURNING user_id"
        )
    )
    row = service.end_relationship_for_complaint(calendar_db, rid, admin)
    assert row.status == "ended"
    assert row.ended_reason == "complaint"
    assert row.ended_by == admin


def test_relationship_payload_normalizes_code_and_forbids_identity_spoofing():
    assert util.find_spec("backend.app.schemas.mentorship") is not None
    from backend.app.schemas.mentorship import MentorshipCreate
    from pydantic import ValidationError

    assert MentorshipCreate(code="  abcdefghjklm  ").code == "ABCDEFGHJKLM"
    for payload in (
        {"code": "short"},
        {"code": "ABCDEFGHIJKL"},
        {"code": "ABCDEFGHJKLM", "mentor_id": 1},
    ):
        with pytest.raises(ValidationError):
            MentorshipCreate(**payload)
