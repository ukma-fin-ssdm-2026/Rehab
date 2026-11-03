"""Schema contracts against isolated PostgreSQL, never a production database."""

import datetime as dt
import re
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

ROOT = Path(__file__).resolve().parents[1]
CODE = re.compile(r"[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{12}")


def test_old_sql_inserts_receive_private_defaults(calendar_db, db_users):
    rows = (
        calendar_db.execute(
            text(
                "SELECT mentor_code,email_reminders_enabled,message_style "
                "FROM users ORDER BY user_id"
            )
        )
        .mappings()
        .all()
    )
    assert len(rows) == 2
    assert all(CODE.fullmatch(row["mentor_code"]) for row in rows)
    assert rows[0]["mentor_code"] != rows[1]["mentor_code"]
    assert all(row["email_reminders_enabled"] is False for row in rows)
    assert all(row["message_style"] == "formal" for row in rows)


def test_existing_registration_and_login_work_after_upgrade(
    authenticated_calendar, registered_users, calendar_db
):
    account, headers = registered_users[0]
    row = calendar_db.execute(
        text("SELECT mentor_code FROM users WHERE user_id=:id"),
        {"id": account["user_id"]},
    ).scalar_one()
    assert CODE.fullmatch(row)
    assert "mentor_code" not in account
    me = authenticated_calendar.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == account["email"]
    assert "mentor_code" not in me.json()


def relationship(db, mentor, mentee):
    return db.scalar(
        text(
            "INSERT INTO mentorships(mentor_id,mentee_id) VALUES (:mentor,:mentee) "
            "RETURNING relationship_id"
        ),
        {"mentor": mentor, "mentee": mentee},
    )


def test_only_one_active_mentor_but_multiple_mentees(calendar_db, db_users):
    first, second = db_users
    third = calendar_db.scalar(
        text(
            "INSERT INTO users(email,name,nickname,password_hash,tracking_start_date) "
            "VALUES ('third@example.test','Third','third','test-hash',CURRENT_DATE) "
            "RETURNING user_id"
        )
    )
    relationship(calendar_db, first, second)
    relationship(calendar_db, first, third)
    with pytest.raises(IntegrityError):
        with calendar_db.begin_nested():
            relationship(calendar_db, third, second)
    with pytest.raises(IntegrityError):
        with calendar_db.begin_nested():
            relationship(calendar_db, first, first)


def test_ended_pair_cannot_be_recreated_and_history_survives(calendar_db, db_users):
    first, second = db_users
    rid = relationship(calendar_db, first, second)
    notification_id = calendar_db.scalar(
        text(
            "INSERT INTO notifications(recipient_id,sender_id,kind,event_key,"
            "business_date,relationship_id) VALUES "
            "(:mentor,:mentee,'relapse','relapse:2:2026-10-30','2026-10-30',:rid) "
            "RETURNING notification_id"
        ),
        {"mentor": first, "mentee": second, "rid": rid},
    )
    calendar_db.execute(
        text(
            "UPDATE mentorships SET status='ended',ended_at=now(),"
            "ended_by=:mentee,ended_reason='mentee_left' WHERE relationship_id=:id"
        ),
        {"id": rid, "mentee": second},
    )
    with pytest.raises(IntegrityError):
        with calendar_db.begin_nested():
            relationship(calendar_db, first, second)
    assert (
        calendar_db.scalar(
            text("SELECT relationship_id FROM notifications WHERE notification_id=:id"),
            {"id": notification_id},
        )
        == rid
    )


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE users SET message_style='unknown' WHERE user_id=:first",
        "UPDATE users SET mentor_code='guessable' WHERE user_id=:first",
        "UPDATE users SET mentor_code=(SELECT mentor_code FROM users "
        "WHERE user_id=:second) WHERE user_id=:first",
        "INSERT INTO mentorships(mentor_id,mentee_id,status) "
        "VALUES (:first,:second,'ended')",
        "INSERT INTO mentorships(mentor_id,mentee_id,status,ended_at,ended_by) "
        "VALUES (:first,:second,'ended',now(),:first)",
        "INSERT INTO notifications(recipient_id,kind,event_key,business_date) "
        "VALUES (:first,'unknown','invalid',CURRENT_DATE)",
        "INSERT INTO email_reminder_deliveries(notification_id,recipient_id,"
        "business_date,status) VALUES (999,:first,CURRENT_DATE,'pending')",
    ],
)
def test_database_rejects_invalid_contract_data(calendar_db, db_users, statement):
    first, second = db_users
    with pytest.raises(IntegrityError):
        with calendar_db.begin_nested():
            calendar_db.execute(text(statement), {"first": first, "second": second})


def test_duplicate_events_and_daily_email_tasks_are_rejected(calendar_db, db_users):
    first, _ = db_users
    params = {"uid": first}
    sql = text(
        "INSERT INTO notifications(recipient_id,kind,event_key,business_date) "
        "VALUES (:uid,'daily_reminder','reminder:2026-10-30','2026-10-30') "
        "RETURNING notification_id"
    )
    nid = calendar_db.scalar(sql, params)
    with pytest.raises(IntegrityError):
        with calendar_db.begin_nested():
            calendar_db.execute(sql, params)
    delivery = text(
        "INSERT INTO email_reminder_deliveries(notification_id,recipient_id,"
        "business_date) VALUES (:nid,:uid,'2026-10-30')"
    )
    calendar_db.execute(delivery, {"uid": first, "nid": nid})
    with pytest.raises(IntegrityError):
        with calendar_db.begin_nested():
            calendar_db.execute(delivery, {"uid": first, "nid": nid})


def test_models_are_available_to_participant_sessions(calendar_db, db_users):
    from backend.app.db.base import Base
    from backend.app.db import models  # noqa: F401
    from backend.app.db.models.user import User

    required = {
        "user_avatars",
        "mentorships",
        "notifications",
        "support_comments",
        "complaints",
        "email_reminder_deliveries",
    }
    assert required <= set(Base.metadata.tables)
    user = calendar_db.get(User, db_users[0])
    assert CODE.fullmatch(user.mentor_code)
    assert user.email_reminders_enabled is False
    assert user.message_style == "formal"


def test_upgrade_preserves_legacy_data_and_backfills_without_notifications(
    postgres_engine,
):
    schema = "migration_" + uuid4().hex
    config = Config(str(ROOT / "alembic.ini"))
    config.cmd_opts = SimpleNamespace(x=["test_db=true"])
    with postgres_engine.connect() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        conn.execute(text(f'SET search_path TO "{schema}"'))
        conn.commit()
        config.attributes["connection"] = conn
        try:
            command.upgrade(config, "0001_initial")
            uid = conn.scalar(
                text(
                    "INSERT INTO users(email,name,nickname,password_hash,"
                    "tracking_start_date,best_streak,is_blocked) VALUES "
                    "('legacy@example.test','Legacy','legacy','preserved-hash',"
                    "'2026-10-01',7,true) RETURNING user_id"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO day_records(user_id,date,status,created_at) VALUES "
                    "(:id,'2026-10-05','relapse','2026-10-05T12:00:00Z'),"
                    "(:id,'2026-10-06','sober','2026-10-06T12:00:00Z')"
                ),
                {"id": uid},
            )
            conn.commit()
            command.upgrade(config, "head")
            row = (
                conn.execute(text("SELECT * FROM users WHERE user_id=:id"), {"id": uid})
                .mappings()
                .one()
            )
            assert CODE.fullmatch(row["mentor_code"])
            assert row["password_hash"] == "preserved-hash"
            assert row["tracking_start_date"] == dt.date(2026, 10, 1)
            assert row["best_streak"] == 7
            assert row["is_blocked"] is False
            assert conn.scalar(text("SELECT count(*) FROM notifications")) == 0
            dates = conn.execute(
                text("SELECT status,first_relapse_at FROM day_records ORDER BY date")
            ).all()
            assert dates == [
                ("relapse", dt.datetime(2026, 10, 5, 12, tzinfo=dt.timezone.utc)),
                ("sober", None),
            ]
            assert {"mentorships", "support_comments"} <= set(
                inspect(conn).get_table_names(schema=schema)
            )
            conn.commit()
            command.upgrade(config, "head")
            assert conn.scalar(text("SELECT count(*) FROM users")) == 1
            conn.commit()
            command.downgrade(config, "0001_initial")
            assert (
                conn.scalar(text("SELECT password_hash FROM users")) == "preserved-hash"
            )
            assert conn.scalar(text("SELECT count(*) FROM day_records")) == 2
            assert "mentorships" not in inspect(conn).get_table_names(schema=schema)
            conn.commit()
            command.upgrade(config, "head")
            assert conn.scalar(text("SELECT count(*) FROM users")) == 1
        finally:
            conn.rollback()
            conn.execute(text("SET search_path TO public"))
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            conn.commit()
