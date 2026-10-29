# AI-GENERATED START
"""Демо-дані: admin + 2 user-акаунти, вигадані записи й ціль.

Запускається ЯВНО, ніколи автоматично при старті:
    python scripts/seed_demo.py
Повторний запуск не створює дублікатів і не змінює наявні акаунти та їхні паролі.

Облікові дані беруться зі змінних середовища (у репозиторій не потрапляють):
    SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD
    SEED_USER_EMAIL / SEED_USER_PASSWORD        (календар і цілі)
    SEED_BLOCK_EMAIL / SEED_BLOCK_PASSWORD      (акаунт для демо блокування)
Потрібен DATABASE_URL (PostgreSQL) і застосовані міграції.
"""

import datetime as dt
import os
import sys

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from backend.app.core.clock import today_local
from backend.app.db.models.entry import DayRecord
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
DEMO_GOAL_DAYS = 7


def _env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"Не задано змінну середовища {name}")
    return value


def _ensure_user(db, email_var, password_var, name, nickname, role, start):
    email = _env(email_var).lower()
    user = get_user_by_email(db, email)
    if user is None:
        user = User(
            name=name,
            nickname=nickname,
            email=email,
            role=role,
            password_hash=hash_password(_env(password_var)),
            tracking_start_date=start,
        )
        db.add(user)
        db.flush()
    return user


def main() -> None:
    today = today_local()
    start = today - dt.timedelta(days=60)
    with Session(get_engine(), expire_on_commit=False) as db:
        _ensure_user(
            db, "SEED_ADMIN_EMAIL", "SEED_ADMIN_PASSWORD",
            "Admin", "admin", "admin", start,
        )
        demo = _ensure_user(
            db, "SEED_USER_EMAIL", "SEED_USER_PASSWORD",
            "Demo User", "demo", "user", start,
        )
        _ensure_user(
            db, "SEED_BLOCK_EMAIL", "SEED_BLOCK_PASSWORD",
            "Block Me", "blockme", "user", start,
        )

        for days_ago, trigger, drink in DEMO_RELAPSES:
            day = today - dt.timedelta(days=days_ago)
            exists = db.scalar(
                select(DayRecord.record_id).where(
                    DayRecord.user_id == demo.user_id, DayRecord.date == day
                )
            )
            if exists is None:
                db.add(
                    DayRecord(
                        user_id=demo.user_id,
                        date=day,
                        status="relapse",
                        trigger_category=trigger,
                        drinks=[{"type": drink, "volume_ml": 330}],
                    )
                )
        db.execute(
            text(
                "INSERT INTO goals (user_id, target_days) "
                "SELECT :user_id, :days WHERE NOT EXISTS "
                "(SELECT 1 FROM goals WHERE user_id = :user_id)"
            ),
            {"user_id": demo.user_id, "days": DEMO_GOAL_DAYS},
        )
        db.commit()
    print("Seed виконано.")


if __name__ == "__main__":
    main()


# AI-GENERATED END
