"""PostgreSQL calendar router for the coordinated KT-1 switch.

Not registered in main.py until the real auth and progress modules are ready.
AI-GENERATED START: prepared with ChatGPT; HTTP/SQL transaction tests included.
"""

from collections.abc import Callable
import datetime as dt
from importlib import import_module

from fastapi import APIRouter, Depends, Path, Query, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.clock import today_local
from backend.app.db.session import get_db
from backend.app.errors import COMMON_RESPONSES, api_error
from backend.app.models import (
    EntryCreate,
    EntryList,
    EntryOut,
    EntryUpdate,
    ErrorResponse,
)
from backend.app.repositories import entries
from backend.app.security import CurrentUser, get_current_user

router = APIRouter(prefix="/calendar/entries", tags=["Calendar"])
ProgressSync = Callable[[Session, int, dt.date], None]
RESPONSES = {**COMMON_RESPONSES, 404: {"model": ErrorResponse}}


def get_progress_sync() -> ProgressSync:
    """Require Mariia's real implementation; never silently omit progress."""
    module_name = "backend.app.services.progress_sync"
    try:
        return import_module(module_name).recompute_progress
    except ModuleNotFoundError as error:
        if error.name != module_name:
            raise
        raise api_error(
            503,
            "PROGRESS_SYNC_UNAVAILABLE",
            "Перерахунок прогресу ще не підключено. Зміни не збережено.",
        ) from error


def _write(
    db: Session, user: CurrentUser, operation, progress: ProgressSync
) -> EntryOut:
    try:
        result = operation()
        progress(db, user.user_id, today_local())
        db.commit()
        return result
    except entries.EntryNotFound as error:
        db.rollback()
        raise api_error(404, "ENTRY_NOT_FOUND", "Запис не знайдено") from error
    except entries.EntryDateOutOfRange as error:
        db.rollback()
        raise api_error(
            422, "DATE_OUTSIDE_TRACKING", "Дата поза періодом відстеження"
        ) from error
    except entries.EntryEditWindowExpired as error:
        db.rollback()
        raise api_error(
            403,
            "EDIT_WINDOW_EXPIRED",
            "Час на редагування цього запису минув (48 годин)",
        ) from error
    except IntegrityError as error:
        db.rollback()
        constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        if constraint == "uq_day_records_user_date":
            raise api_error(
                409, "ENTRY_ALREADY_EXISTS", "Запис на цю дату вже існує"
            ) from error
        raise
    except Exception:
        db.rollback()
        raise


@router.post(
    "",
    status_code=201,
    response_model=EntryOut,
    summary="Створити відмітку дня",
    responses={
        **RESPONSES,
        409: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def create_entry(
    body: EntryCreate,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    progress: ProgressSync = Depends(get_progress_sync),
):
    result = _write(
        db, user, lambda: entries.create_entry(db, user.user_id, body), progress
    )
    response.headers["Location"] = f"{request.url.path.rstrip('/')}/{result.record_id}"
    return result


@router.get("", response_model=EntryList, responses=RESPONSES)
def list_entries(
    date_from: dt.date | None = Query(None, alias="from"),
    date_to: dt.date | None = Query(None, alias="to"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if date_from and date_to and date_from > date_to:
        raise api_error(422, "INVALID_DATE_RANGE", "Початок періоду пізніше завершення")
    return EntryList(
        items=entries.list_user_entries(
            db, user.user_id, date_from, date_to, limit=limit, offset=offset
        ),
        total=entries.count_user_entries(db, user.user_id, date_from, date_to),
        limit=limit,
        offset=offset,
    )


@router.get("/{record_id}", response_model=EntryOut, responses=RESPONSES)
def get_entry(
    record_id: int = Path(..., ge=1),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return entries.get_own_entry(db, user.user_id, record_id)
    except entries.EntryNotFound as error:
        raise api_error(404, "ENTRY_NOT_FOUND", "Запис не знайдено") from error


@router.patch(
    "/{record_id}",
    response_model=EntryOut,
    responses={
        **RESPONSES,
        403: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def update_entry(
    body: EntryUpdate,
    record_id: int = Path(..., ge=1),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    progress: ProgressSync = Depends(get_progress_sync),
):
    return _write(
        db,
        user,
        lambda: entries.update_entry(db, user.user_id, record_id, body),
        progress,
    )


# AI-GENERATED END
