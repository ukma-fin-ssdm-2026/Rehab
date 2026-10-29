"""Calendar persistence shared with statistics and administrator analytics.

AI-GENERATED START: prepared with ChatGPT; real PostgreSQL regression tests.
"""

import datetime as dt

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from backend.app.core.clock import today_local, utc_now
from backend.app.db.models.entry import DayRecord
from backend.app.models import DayStatus, EntryCreate, EntryOut, EntryUpdate

EDIT_WINDOW = dt.timedelta(hours=48)


class EntryNotFound(LookupError):
    """No visible record, including a record belonging to another user."""


class EntryEditWindowExpired(ValueError):
    """More than 48 hours passed since the original creation timestamp."""


class EntryDateOutOfRange(ValueError):
    """Date is outside the account's tracking interval."""


def _tracking_start(db: Session, user_id: int) -> dt.date:
    # Serialize mutations for one user so a future statistics recomputation
    # observes a complete history within the same transaction.
    start = db.scalar(
        text("SELECT tracking_start_date FROM users WHERE user_id=:id FOR UPDATE"),
        {"id": user_id},
    )
    if start is None:
        raise EntryDateOutOfRange("Tracking has not started for this account")
    return start


def _out(record: DayRecord) -> EntryOut:
    return EntryOut.model_validate(record, from_attributes=True)


def create_entry(db: Session, user_id: int, body: EntryCreate) -> EntryOut:
    start = _tracking_start(db, user_id)
    if not start <= body.date <= today_local():
        raise EntryDateOutOfRange("Date must be within the tracking interval")
    record = DayRecord(
        user_id=user_id,
        date=body.date,
        status=body.status.value,
        trigger_category=body.trigger_category.value if body.trigger_category else None,
        drinks=[drink.model_dump(mode="json") for drink in body.drinks],
        comment=body.comment,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(record)
    db.flush()
    return _out(record)


def _own_record(db: Session, user_id: int, record_id: int, *, lock=False):
    query = select(DayRecord).where(
        DayRecord.user_id == user_id, DayRecord.record_id == record_id
    )
    if lock:
        query = query.with_for_update()
    record = db.scalar(query)
    if record is None:
        raise EntryNotFound("Entry not found")
    return record


def get_own_entry(db: Session, user_id: int, record_id: int) -> EntryOut:
    return _out(_own_record(db, user_id, record_id))


def update_entry(
    db: Session, user_id: int, record_id: int, body: EntryUpdate
) -> EntryOut:
    _tracking_start(db, user_id)
    record = _own_record(db, user_id, record_id, lock=True)
    now = utc_now()
    if now - record.created_at > EDIT_WINDOW:
        raise EntryEditWindowExpired("The 48-hour edit window has expired")
    record.status = body.status.value
    record.trigger_category = (
        body.trigger_category.value if body.trigger_category else None
    )
    if body.status == DayStatus.sober:
        record.drinks = []
    record.updated_at = now
    db.flush()
    return _out(record)


def _filter(query, user_id, date_from, date_to):
    if date_from and date_to and date_from > date_to:
        raise ValueError("Date range is reversed")
    query = query.where(DayRecord.user_id == user_id)
    if date_from:
        query = query.where(DayRecord.date >= date_from)
    if date_to:
        query = query.where(DayRecord.date <= date_to)
    return query


def list_user_entries(
    db: Session,
    user_id: int,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    *,
    limit: int | None = None,
    offset: int = 0,
) -> list[EntryOut]:
    query = _filter(select(DayRecord), user_id, date_from, date_to)
    query = query.order_by(DayRecord.date.desc(), DayRecord.record_id.desc())
    if limit is not None:
        query = query.limit(limit)
    return [_out(record) for record in db.scalars(query.offset(offset))]


def count_user_entries(
    db: Session,
    user_id: int,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> int:
    query = _filter(
        select(func.count()).select_from(DayRecord), user_id, date_from, date_to
    )
    return db.scalar(query)


def list_relapse_entries(
    db: Session, date_from: dt.date, date_to: dt.date
) -> list[EntryOut]:
    if date_from > date_to:
        raise ValueError("Date range is reversed")
    query = select(DayRecord).where(
        DayRecord.status == DayStatus.relapse.value,
        DayRecord.date >= date_from,
        DayRecord.date <= date_to,
    )
    return [_out(record) for record in db.scalars(query)]


# AI-GENERATED END
