# AI-GENERATED START
"""Службовий запуск нагадувань за розкладом (ТЗ С-4).

Не користувацький маршрут: без JWT і ролі admin, лише секрет X-Job-Token.
Немає GET-запуску, параметрів дати чи отримувача. Паралельні виклики
серіалізує advisory-lock PostgreSQL; повтори зупиняють унікальні ключі.
"""

import hmac
import logging
import os
from collections.abc import Callable
from contextlib import contextmanager

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field

from backend.app.errors import api_error
from backend.app.models import ErrorResponse

router = APIRouter(prefix="/internal/jobs", tags=["Jobs"])
log = logging.getLogger(__name__)

# Довільна стала 64-бітна мітка саме цього job у pg_advisory_lock.
JOB_LOCK_KEY = 0x5245_4841_4252_454D


class ReminderJobResult(BaseModel):
    created_in_app: int = Field(..., ge=0)
    queued_email: int = Field(..., ge=0)
    sent: int = Field(..., ge=0)
    skipped: int = Field(..., ge=0, description="Пропущені нагадування й листи.")
    failed: int = Field(..., ge=0)
    unknown: int = Field(..., ge=0)


def get_engine_for_job():
    from backend.app.db.session import get_engine

    return get_engine()


def get_reminder_creator() -> Callable:
    try:
        from backend.app.services.reminders import create_due_reminders
    except ImportError:
        raise api_error(
            503, "REMINDERS_NOT_READY", "Створення нагадувань ще не підключено"
        ) from None
    return create_due_reminders


def get_sender():
    from backend.app.services.email_reminders import sender_from_env

    return sender_from_env()


def get_clock() -> Callable:
    from backend.app.core.clock import utc_now

    return utc_now


def require_job_token(x_job_token: str | None = Header(None)) -> None:
    expected = os.getenv("REMINDERS_JOB_TOKEN", "")
    if len(expected) < 32:
        raise api_error(503, "JOB_NOT_CONFIGURED", "Секрет job не налаштовано")
    if not x_job_token or not hmac.compare_digest(
        x_job_token.encode(), expected.encode()
    ):
        raise api_error(401, "INVALID_JOB_TOKEN", "Недійсний секрет job")


@contextmanager
def job_lock(engine):
    """Окреме autocommit-з'єднання: лок без відкритої транзакції даних."""
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        from sqlalchemy import text

        acquired = conn.scalar(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": JOB_LOCK_KEY}
        )
        try:
            yield acquired
        finally:
            if acquired:
                conn.execute(
                    text("SELECT pg_advisory_unlock(:key)"), {"key": JOB_LOCK_KEY}
                )


@router.post(
    "/reminders",
    response_model=ReminderJobResult,
    dependencies=[Depends(require_job_token)],
    responses={
        401: {"model": ErrorResponse, "description": "Недійсний секрет"},
        409: {"model": ErrorResponse, "description": "Job уже виконується"},
        503: {"model": ErrorResponse, "description": "Job не налаштовано"},
    },
)
def run_reminders(
    engine=Depends(get_engine_for_job),
    create_due_reminders: Callable = Depends(get_reminder_creator),
    sender=Depends(get_sender),
    clock: Callable = Depends(get_clock),
) -> ReminderJobResult:
    """Створює нагадування за поточну київську дату й обробляє поштову чергу."""
    from sqlalchemy.orm import Session

    from backend.app.services.email_reminders import deliver_pending_reminders

    def db_factory() -> Session:
        return Session(engine, expire_on_commit=False)

    with job_lock(engine) as acquired:
        if not acquired:
            raise api_error(409, "JOB_ALREADY_RUNNING", "Job уже виконується")
        now = clock()
        with db_factory() as db:
            created = create_due_reminders(db, now)
            db.commit()
        if sender is None:
            # Листи лишаються в черзі pending; наступної доби їх позначить skipped.
            log.warning("reminder job: GMAIL_NOT_CONFIGURED")
            delivered = {"sent": 0, "skipped": 0, "failed": 0, "unknown": 0}
        else:
            delivered = deliver_pending_reminders(db_factory, now, sender, clock)
    return ReminderJobResult(
        created_in_app=created.get("created_in_app", 0),
        queued_email=created.get("queued_email", 0),
        sent=delivered["sent"],
        skipped=created.get("skipped", 0) + delivered["skipped"],
        failed=delivered["failed"],
        unknown=delivered["unknown"],
    )


# AI-GENERATED END
