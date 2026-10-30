# AI-GENERATED START
"""seed_demo ідемпотентний і не відновлює завершені пари (ТЗ С-5)."""

import datetime as dt

from sqlalchemy import func, select

from backend.app.db.models.entry import DayRecord
from backend.app.db.models.mentorship import Mentorship
from backend.app.db.models.notification import Notification
from backend.app.db.models.user import User
from scripts import seed_demo

PREFIXES = ("ADMIN", "MENTOR", "USER", "PAIR2_MENTOR", "PAIR2_MENTEE")


def configure(monkeypatch, engine):
    for prefix in PREFIXES:
        monkeypatch.setenv(f"SEED_{prefix}_EMAIL", f"{prefix.lower()}@seed.test")
        monkeypatch.setenv(f"SEED_{prefix}_PASSWORD", "seed-password-1")
    monkeypatch.setattr(seed_demo, "get_engine", lambda: engine)


def count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def test_seed_is_idempotent_and_creates_two_pairs(
    calendar_db, postgres_schema, monkeypatch
):
    configure(monkeypatch, postgres_schema)

    seed_demo.main()
    first = (count(calendar_db, User), count(calendar_db, DayRecord))
    hashes = dict(calendar_db.execute(select(User.email, User.password_hash)).all())
    seed_demo.main()

    assert first == (5, 12)
    assert (count(calendar_db, User), count(calendar_db, DayRecord)) == first
    assert dict(calendar_db.execute(select(User.email, User.password_hash)).all()) == (
        hashes
    )
    assert count(calendar_db, Mentorship) == 2
    assert set(calendar_db.scalars(select(Mentorship.status))) == {"active"}
    assert count(calendar_db, Notification) == 0
    relapses = calendar_db.scalars(
        select(DayRecord).where(DayRecord.status == "relapse")
    ).all()
    assert relapses and all(r.first_relapse_at is not None for r in relapses)


def test_seed_does_not_restore_ended_pair(calendar_db, postgres_schema, monkeypatch):
    configure(monkeypatch, postgres_schema)
    seed_demo.main()
    pair = calendar_db.scalars(select(Mentorship)).first()
    pair.status = "ended"
    pair.ended_at = dt.datetime.now(dt.timezone.utc)
    pair.ended_by = pair.mentee_id
    pair.ended_reason = "mentee_left"
    calendar_db.commit()

    seed_demo.main()

    calendar_db.expire_all()
    assert calendar_db.get(Mentorship, pair.relationship_id).status == "ended"
    assert count(calendar_db, Mentorship) == 2


# AI-GENERATED END
