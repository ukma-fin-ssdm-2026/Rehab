# AI-GENERATED START
"""Поштова копія щоденного нагадування через Gmail API (ТЗ С-3).

Черга — таблиця email_reminder_deliveries. Кожен рядок захоплює один worker
(status=sending) у короткій транзакції; мережевий запит до Gmail іде поза
транзакцією. Невизначений результат (таймаут, розрив, падіння між Gmail і
збереженням) → unknown без сліпого повтору: exactly-once зовнішня пошта не обіцяє.
Журнали містять лише delivery_id і код помилки — без адрес, текстів і токенів.
"""

import base64
import datetime as dt
import logging
import os
from collections.abc import Callable
from email.message import EmailMessage
from typing import Protocol

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.app.core.clock import BUSINESS_TIMEZONE
from backend.app.db.models.email_delivery import EmailReminderDelivery
from backend.app.db.models.entry import DayRecord
from backend.app.db.models.user import User

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
SENDING_TIMEOUT = dt.timedelta(minutes=5)
SUBJECT = "Нагадування Rehab"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.send"
GOOGLE_OAUTH_EXCHANGE_URL = "https://oauth2.googleapis.com/token"


class SendRejected(Exception):
    """Gmail явно не прийняв лист: можна повторити в межах MAX_ATTEMPTS."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class SendUncertain(Exception):
    """Невідомо, чи лист пішов: результат unknown, без автоматичного повтору."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class Sender(Protocol):
    def send(self, to: str, subject: str, body: str) -> str:
        """Повертає provider_message_id або кидає SendRejected/SendUncertain."""


def build_message(mail_from: str, to: str, subject: str, body: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = mail_from
    message["Reply-To"] = mail_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    return message


class GmailSender:
    """Надсилання від rehab.support.web@gmail.com, scope лише gmail.send."""

    def __init__(self, client_id, client_secret, refresh_token, mail_from):
        from google.auth.transport.requests import AuthorizedSession
        from google.oauth2.credentials import Credentials

        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri=GOOGLE_OAUTH_EXCHANGE_URL,
            scopes=[GMAIL_SCOPE],
        )
        self._session = AuthorizedSession(credentials)
        self.mail_from = mail_from

    def send(self, to: str, subject: str, body: str) -> str:
        import requests
        from google.auth.exceptions import RefreshError, TransportError

        raw = base64.urlsafe_b64encode(
            build_message(self.mail_from, to, subject, body).as_bytes()
        ).decode("ascii")
        try:
            response = self._session.post(
                GMAIL_SEND_URL, json={"raw": raw}, timeout=(5, 20)
            )
        except (RefreshError, TransportError):
            raise SendRejected("GMAIL_AUTH") from None
        except requests.ConnectTimeout:
            raise SendRejected("GMAIL_CONNECT") from None
        except requests.RequestException:
            raise SendUncertain("GMAIL_NETWORK") from None
        if response.status_code != 200:
            raise SendRejected(f"GMAIL_HTTP_{response.status_code}")
        message_id = response.json().get("id")
        if not message_id:
            raise SendUncertain("GMAIL_NO_ID")
        return message_id


def sender_from_env() -> GmailSender | None:
    names = (
        "GMAIL_CLIENT_ID",
        "GMAIL_CLIENT_SECRET",
        "GMAIL_REFRESH_TOKEN",
        "MAIL_FROM",
    )
    values = [os.getenv(name, "").strip() for name in names]
    return GmailSender(*values) if all(values) else None


def calendar_url() -> str:
    """Перша HTTPS-адреса frontend із CORS_ORIGINS (без секретів)."""
    for origin in os.getenv("CORS_ORIGINS", "").split(","):
        origin = origin.strip().rstrip("/")
        if origin.startswith("https://"):
            return f"{origin}/calendar"
    return ""


def reminder_body(style: str) -> str:
    from backend.app.services.message_texts import render_message

    _, body = render_message("daily_reminder", style, {})
    link = calendar_url()
    return f"{body}\n\nКалендар: {link}" if link else body


def _counts() -> dict[str, int]:
    return {"sent": 0, "skipped": 0, "failed": 0, "unknown": 0}


def _housekeeping(db: Session, now: dt.datetime, today: dt.date) -> None:
    db.execute(
        update(EmailReminderDelivery)
        .where(
            EmailReminderDelivery.status == "sending",
            EmailReminderDelivery.claimed_at < now - SENDING_TIMEOUT,
        )
        .values(status="unknown", last_error_code="SENDING_TIMEOUT")
    )
    db.execute(
        update(EmailReminderDelivery)
        .where(
            EmailReminderDelivery.status.in_(("pending", "failed")),
            EmailReminderDelivery.business_date < today,
        )
        .values(status="skipped", last_error_code="EXPIRED")
    )


def _claim(
    db: Session, now: dt.datetime, today: dt.date, seen: set[int]
) -> EmailReminderDelivery | None:
    # Повтор після відмови — у наступному запуску розкладу, не в тому самому.
    delivery = db.scalar(
        select(EmailReminderDelivery)
        .where(
            EmailReminderDelivery.status.in_(("pending", "failed")),
            EmailReminderDelivery.business_date == today,
            EmailReminderDelivery.attempts < MAX_ATTEMPTS,
            EmailReminderDelivery.delivery_id.not_in(seen),
        )
        .order_by(EmailReminderDelivery.delivery_id)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    if delivery is not None:
        delivery.status = "sending"
        delivery.claimed_at = now
        delivery.attempts += 1
    return delivery


def _still_wanted(db: Session, delivery: EmailReminderDelivery) -> User | None:
    user = db.get(User, delivery.recipient_id)
    if user is None or not user.email_reminders_enabled:
        return None
    has_entry = db.scalar(
        select(DayRecord.record_id).where(
            DayRecord.user_id == user.user_id,
            DayRecord.date == delivery.business_date,
        )
    )
    return None if has_entry is not None else user


def _finish(db_factory, delivery_id: int, **values) -> None:
    with db_factory() as db:
        db.execute(
            update(EmailReminderDelivery)
            .where(EmailReminderDelivery.delivery_id == delivery_id)
            .values(**values)
        )
        db.commit()


def maintain_reminder_queue(
    db_factory: Callable[[], Session], now: dt.datetime
) -> None:
    """Expire old work even when Gmail credentials are not configured."""
    if now.tzinfo is None:
        raise ValueError("now має містити часовий пояс")
    with db_factory() as db:
        _housekeeping(db, now, now.astimezone(BUSINESS_TIMEZONE).date())
        db.commit()


def deliver_pending_reminders(
    db_factory: Callable[[], Session],
    now: dt.datetime,
    sender: Sender,
    clock: Callable[[], dt.datetime] | None = None,
) -> dict[str, int]:
    """Обробляє чергу поточної київської дати; повертає лічильники результатів.

    now — момент запуску; clock (за замовчуванням now) — поточний час перед
    кожним листом, щоб не надіслати прострочене після київської півночі.
    """
    if now.tzinfo is None:
        raise ValueError("now має містити часовий пояс")
    clock = clock or (lambda: now)
    today = now.astimezone(BUSINESS_TIMEZONE).date()
    counts = _counts()
    seen: set[int] = set()
    maintain_reminder_queue(db_factory, now)

    while True:
        current = clock()
        if current.astimezone(BUSINESS_TIMEZONE).date() != today:
            break
        with db_factory() as db:
            delivery = _claim(db, current, today, seen)
            if delivery is None:
                db.commit()
                break
            delivery_id = delivery.delivery_id
            seen.add(delivery_id)
            user = _still_wanted(db, delivery)
            if user is None:
                delivery.status = "skipped"
                delivery.last_error_code = "NOT_WANTED"
                db.commit()
                counts["skipped"] += 1
                continue
            to, style = user.email, user.message_style
            db.commit()

        try:
            message_id = sender.send(to, SUBJECT, reminder_body(style))
        except SendRejected as error:
            log.warning("email delivery %s rejected: %s", delivery_id, error.code)
            _finish(
                db_factory, delivery_id, status="failed", last_error_code=error.code
            )
            counts["failed"] += 1
            continue
        except Exception as error:  # noqa: BLE001 — будь-який інший збій невизначений
            code = getattr(error, "code", "SEND_UNCERTAIN")
            log.warning("email delivery %s uncertain: %s", delivery_id, code)
            _finish(db_factory, delivery_id, status="unknown", last_error_code=code)
            counts["unknown"] += 1
            continue
        _finish(
            db_factory,
            delivery_id,
            status="sent",
            sent_at=clock(),
            provider_message_id=message_id,
            last_error_code=None,
        )
        counts["sent"] += 1
    return counts


# AI-GENERATED END
