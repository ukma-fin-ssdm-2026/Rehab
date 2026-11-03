"""Calendar persistence and ownership against actual PostgreSQL, not stubs."""

from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import importlib
from threading import Barrier

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.clock import today_local
from backend.app.core.config import get_database_url
from backend.app.models import EntryCreate, EntryUpdate


def repository():
    return importlib.import_module("backend.app.repositories.entries")


def entry_body(**changes):
    return EntryCreate.model_validate(
        {"date": today_local(), "status": "sober", **changes}
    )


def test_entry_survives_new_engine_and_stub_reset(calendar_db, db_users):
    repo = repository()
    created = repo.create_entry(
        calendar_db,
        db_users[0],
        entry_body(
            status="relapse",
            trigger_category="stress",
            drinks=[{"type": "wine", "volume_ml": 150}],
            comment="Persistence probe",
        ),
    )
    calendar_db.commit()
    from backend.app import stubs

    stubs.reset()
    new_engine = create_engine(get_database_url(test=True))
    try:
        with Session(new_engine) as other:
            found = repo.get_own_entry(other, db_users[0], created.record_id)
            assert found.comment == "Persistence probe"
            assert found.drinks[0].volume_ml == 150
            assert found.created_at.utcoffset() == dt.timedelta(0)
    finally:
        new_engine.dispose()


def test_repository_does_not_commit_callers_transaction(calendar_db, db_users):
    repo = repository()
    repo.create_entry(calendar_db, db_users[0], entry_body())
    calendar_db.rollback()
    assert repo.list_user_entries(calendar_db, db_users[0]) == []


def test_calendar_queries_filter_owner_dates_and_page(calendar_db, db_users):
    repo = repository()
    today = today_local()
    for day in range(3):
        repo.create_entry(
            calendar_db, db_users[0], entry_body(date=today - dt.timedelta(days=day))
        )
    other = repo.create_entry(calendar_db, db_users[1], entry_body())
    calendar_db.commit()
    assert len(repo.list_user_entries(calendar_db, db_users[0])) == 3
    page = repo.list_user_entries(
        calendar_db,
        db_users[0],
        date_from=today - dt.timedelta(days=1),
        limit=1,
        offset=1,
    )
    assert [item.date for item in page] == [today - dt.timedelta(days=1)]
    assert repo.count_user_entries(calendar_db, db_users[0], date_from=today) == 1
    with pytest.raises(repo.EntryNotFound):
        repo.get_own_entry(calendar_db, db_users[0], other.record_id)


@pytest.mark.parametrize(
    "elapsed,allowed", [(172799, True), (172800, True), (172801, False)]
)
def test_exact_edit_window_and_original_creation_time(
    calendar_db, db_users, monkeypatch, elapsed, allowed
):
    repo = repository()
    created = repo.create_entry(
        calendar_db,
        db_users[0],
        entry_body(status="relapse", trigger_category="social"),
    )
    calendar_db.commit()
    instant = dt.datetime(2026, 10, 29, 12, tzinfo=dt.timezone.utc)
    original = instant - dt.timedelta(seconds=elapsed)
    calendar_db.execute(
        text("UPDATE day_records SET created_at=:created WHERE record_id=:id"),
        {"created": original, "id": created.record_id},
    )
    calendar_db.commit()
    calendar_db.expire_all()
    monkeypatch.setattr(repo, "utc_now", lambda: instant)
    body = EntryUpdate(status="sober")
    if allowed:
        result = repo.update_entry(calendar_db, db_users[0], created.record_id, body)
        calendar_db.commit()
        assert result.created_at == original
        assert result.status.value == "sober"
        assert result.trigger_category is None
        assert result.drinks == []
    else:
        with pytest.raises(repo.EntryEditWindowExpired):
            repo.update_entry(calendar_db, db_users[0], created.record_id, body)
        calendar_db.rollback()
        assert (
            repo.get_own_entry(calendar_db, db_users[0], created.record_id).status.value
            == "relapse"
        )


def test_entry_before_tracking_start_is_rejected(calendar_db, db_users):
    repo = repository()
    with pytest.raises(repo.EntryDateOutOfRange):
        repo.create_entry(
            calendar_db,
            db_users[0],
            entry_body(date=today_local() - dt.timedelta(days=31)),
        )


def test_anonymous_relapse_source_only_includes_requested_period(calendar_db, db_users):
    repo = repository()
    today = today_local()
    repo.create_entry(calendar_db, db_users[0], entry_body(status="relapse"))
    repo.create_entry(
        calendar_db,
        db_users[1],
        entry_body(date=today - dt.timedelta(days=30), status="relapse"),
    )
    calendar_db.commit()
    rows = repo.list_relapse_entries(calendar_db, today - dt.timedelta(days=29), today)
    assert len(rows) == 1
    assert rows[0].date == today


def test_concurrent_duplicate_creates_one_record(
    calendar_db, db_users, postgres_schema
):
    repo = repository()
    barrier = Barrier(2)

    def insert():
        with Session(postgres_schema) as session:
            barrier.wait(timeout=10)
            try:
                repo.create_entry(session, db_users[0], entry_body())
                session.commit()
                return "created"
            except IntegrityError:
                session.rollback()
                return "duplicate"

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(lambda _: insert(), range(2))) == [
            "created",
            "duplicate",
        ]
    assert repo.count_user_entries(calendar_db, db_users[0]) == 1


def test_get_db_rolls_back_failed_request(
    calendar_db, db_users, monkeypatch, postgres_schema
):
    from backend.app.db import session as sessions

    monkeypatch.setattr(sessions, "get_engine", lambda: postgres_schema)
    request = sessions.get_db()
    db = next(request)
    db.execute(
        text("INSERT INTO goals(user_id,target_days) VALUES (:id,10)"),
        {"id": db_users[0]},
    )
    with pytest.raises(RuntimeError, match="request failed"):
        request.throw(RuntimeError("request failed"))
    assert calendar_db.scalar(text("SELECT count(*) FROM goals")) == 0
