# AI-GENERATED START
"""Демо-дані: admin, дві пари ментор/підопічний і календар sober/relapse.

Запускається ЯВНО, ніколи автоматично при старті:
    python -m scripts.seed_demo   (з кореня репозиторію; так видно пакет backend)

Ідемпотентно: повторний запуск не створює дублікатів, не змінює наявні акаунти,
їхні паролі чи завершені зв'язки, не очищує таблиці. Повідомлень, історичних
подій зриву й листів seed не створює.

Облікові дані беруться зі змінних середовища (у репозиторій не потрапляють):
    SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD
    SEED_MENTOR_EMAIL / SEED_MENTOR_PASSWORD      ментор пари 1
    SEED_USER_EMAIL / SEED_USER_PASSWORD          підопічний пари 1, календар
    SEED_PAIR2_MENTOR_EMAIL / SEED_PAIR2_MENTOR_PASSWORD   пара 2: для завершення
    SEED_PAIR2_MENTEE_EMAIL / SEED_PAIR2_MENTEE_PASSWORD   або демо скарги
Потрібен DATABASE_URL (PostgreSQL) і застосовані міграції.
"""

import datetime as dt
import os
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.clock import today_local, utc_now
from backend.app.db.models.entry import DayRecord
from backend.app.db.models.mentorship import Mentorship
from backend.app.db.models.user import User
from backend.app.db.session import get_engine
from backend.app.repositories.users import get_user_by_email
from backend.app.services.auth import hash_password

# (днів тому, тригер, напій): вигадані дані для наочної діаграми
DEMO_RELAPSES = [
    (2, "stress", "beer"),
    (5, "stress", "wine"),
    (8, "stress", "spirits"),
    (11, "holiday", "wine"),
    (14, "holiday", "cocktail"),
    (18, "social", "beer"),
    (22, "other", "beer"),
    (26, "stress", "beer"),
]
PAIR2_RELAPSES = [(3, "social", "cocktail")]
PAIR2_SOBER_DAYS = (1, 2, 4)


def _env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"Не задано змінну середовища {name}")
    return value


def _ensure_user(db, prefix, name, nickname, role, start):
    email = _env(f"{prefix}_EMAIL").lower()
    user = get_user_by_email(db, email)
    if user is None:
        user = User(
            name=name,
            nickname=nickname,
            email=email,
            role=role,
            password_hash=hash_password(_env(f"{prefix}_PASSWORD")),
            tracking_start_date=start,
        )
        db.add(user)
        db.flush()
    return user


def _ensure_pair(db, mentor, mentee) -> str:
    """Не відновлює завершену пару і не замінює чинного ментора."""
    pair = db.scalar(
        select(Mentorship).where(
            Mentorship.mentor_id == mentor.user_id,
            Mentorship.mentee_id == mentee.user_id,
        )
    )
    if pair is not None:
        return pair.status
    other = db.scalar(
        select(Mentorship.relationship_id).where(
            Mentorship.mentee_id == mentee.user_id, Mentorship.status == "active"
        )
    )
    if other is not None:
        return "skipped: mentee has another mentor"
    db.add(Mentorship(mentor_id=mentor.user_id, mentee_id=mentee.user_id))
    db.flush()
    return "created"


def _ensure_entry(db, user, day, status, trigger=None, drink=None) -> None:
    exists = db.scalar(
        select(DayRecord.record_id).where(
            DayRecord.user_id == user.user_id, DayRecord.date == day
        )
    )
    if exists is not None:
        return
    relapse = status == "relapse"
    db.add(
        DayRecord(
            user_id=user.user_id,
            date=day,
            status=status,
            trigger_category=trigger,
            drinks=[{"type": drink, "volume_ml": 330}] if relapse else [],
            # Історичний зрив уже «відбувся»: ментору про нього не повідомляємо.
            first_relapse_at=utc_now() if relapse else None,
        )
    )


def main() -> None:
    today = today_local()
    start = today - dt.timedelta(days=60)
    with Session(get_engine(), expire_on_commit=False) as db:
        _ensure_user(db, "SEED_ADMIN", "Admin", "admin", "admin", start)
        mentor = _ensure_user(db, "SEED_MENTOR", "Demo Mentor", "mentor", "user", start)
        demo = _ensure_user(db, "SEED_USER", "Demo User", "demo", "user", start)
        mentor2 = _ensure_user(
            db, "SEED_PAIR2_MENTOR", "Second Mentor", "mentor2", "user", start
        )
        mentee2 = _ensure_user(
            db, "SEED_PAIR2_MENTEE", "Second Mentee", "mentee2", "user", start
        )

        for days_ago, trigger, drink in DEMO_RELAPSES:
            day = today - dt.timedelta(days=days_ago)
            _ensure_entry(db, demo, day, "relapse", trigger, drink)
        for days_ago, trigger, drink in PAIR2_RELAPSES:
            day = today - dt.timedelta(days=days_ago)
            _ensure_entry(db, mentee2, day, "relapse", trigger, drink)
        for days_ago in PAIR2_SOBER_DAYS:
            _ensure_entry(db, mentee2, today - dt.timedelta(days=days_ago), "sober")

        pairs = [_ensure_pair(db, mentor, demo), _ensure_pair(db, mentor2, mentee2)]
        db.commit()
    print(f"Seed виконано. Пари: {', '.join(pairs)}.")


if __name__ == "__main__":
    main()


# AI-GENERATED END
