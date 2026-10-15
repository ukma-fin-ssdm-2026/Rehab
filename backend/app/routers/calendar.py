"""Ендпоінти календаря відміток (ресурс DayRecord)."""

import datetime as dt

from fastapi import APIRouter, Depends, Path, Query, Request, Response

from backend.app import stubs
from backend.app.errors import COMMON_RESPONSES, api_error
from backend.app.models import (
    DayStatus,
    EntryCreate,
    EntryList,
    EntryOut,
    EntryUpdate,
    ErrorResponse,
)
from backend.app.security import CurrentUser, get_current_user

router = APIRouter(prefix="/calendar/entries", tags=["Calendar"])

EDIT_WINDOW = dt.timedelta(hours=48)


@router.post(
    "",
    status_code=201,
    response_model=EntryOut,
    summary="Створити відмітку дня",
    description=(
        "Відмічає день як тверезий (`sober`) або зрив (`relapse`) для поточного користувача. "
        "Майбутні дати заборонені (FR-002). На одну дату може бути лише один запис. "
        "При зриві серія обнуляється, а ментор отримує сповіщення (FR-003); "
        "у заглушці сповіщення не надсилається."
    ),
    responses={
        **COMMON_RESPONSES,
        201: {
            "description": "Запис створено",
            "headers": {
                "Location": {
                    "description": "URL створеного запису",
                    "schema": {"type": "string"},
                }
            },
        },
        409: {"model": ErrorResponse, "description": "Запис на цю дату вже існує"},
    },
)
def create_entry(
    body: EntryCreate,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
):
    duplicate = any(
        e.user_id == user.user_id and e.date == body.date
        for e in stubs.entries.values()
    )
    if duplicate:
        raise api_error(
            409,
            "ENTRY_ALREADY_EXISTS",
            f"Запис на дату {body.date} уже існує",
            {"date": str(body.date)},
        )

    entry = EntryOut(
        record_id=stubs.next_entry_id(),
        user_id=user.user_id,
        date=body.date,
        status=body.status,
        trigger_category=body.trigger_category,
        drinks=body.drinks,
        comment=body.comment,
        created_at=dt.datetime.now(dt.timezone.utc),
    )
    stubs.entries[entry.record_id] = entry
    response.headers["Location"] = f"{request.url.path.rstrip('/')}/{entry.record_id}"
    return entry


@router.get(
    "",
    response_model=EntryList,
    summary="Отримати список відміток",
    description=(
        "Повертає відмітки поточного користувача, відсортовані від нових до старих. "
        "Підтримує фільтр за діапазоном дат та пагінацію (`limit`, `offset`)."
    ),
    responses={**COMMON_RESPONSES},
)
def list_entries(
    date_from: dt.date | None = Query(
        None,
        alias="from",
        description="Початок діапазону (включно), YYYY-MM-DD.",
    ),
    date_to: dt.date | None = Query(
        None,
        alias="to",
        description="Кінець діапазону (включно), YYYY-MM-DD.",
    ),
    limit: int = Query(30, ge=1, le=100, description="Розмір сторінки (1-100)."),
    offset: int = Query(0, ge=0, description="Скільки записів пропустити."),
    user: CurrentUser = Depends(get_current_user),
):
    if date_from and date_to and date_from > date_to:
        raise api_error(
            422,
            "INVALID_DATE_RANGE",
            "Параметр `from` не може бути пізніше за `to`",
        )

    items = [e for e in stubs.entries.values() if e.user_id == user.user_id]
    if date_from:
        items = [e for e in items if e.date >= date_from]
    if date_to:
        items = [e for e in items if e.date <= date_to]
    items.sort(key=lambda e: e.date, reverse=True)

    return EntryList(
        items=items[offset : offset + limit],
        total=len(items),
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/{record_id}",
    response_model=EntryOut,
    summary="Змінити статус відміченого дня",
    description=(
        "Змінює статус (і тригер) існуючого запису. Дату змінити не можна. "
        "Редагування дозволене лише протягом 48 годин з моменту створення запису (FR-008), "
        "після цього повертається 403."
    ),
    responses={
        **COMMON_RESPONSES,
        403: {
            "model": ErrorResponse,
            "description": "Минуло 48 годин з моменту створення запису",
        },
        404: {"model": ErrorResponse, "description": "Запис не знайдено"},
    },
)
def update_entry(
    body: EntryUpdate,
    record_id: int = Path(..., ge=1, description="Ідентифікатор запису.", examples=[2]),
    user: CurrentUser = Depends(get_current_user),
):
    entry = stubs.entries.get(record_id)
    if entry is None or entry.user_id != user.user_id:
        raise api_error(404, "ENTRY_NOT_FOUND", f"Запис {record_id} не знайдено")

    age = dt.datetime.now(dt.timezone.utc) - entry.created_at
    if age > EDIT_WINDOW:
        raise api_error(
            403,
            "EDIT_WINDOW_EXPIRED",
            "Час на редагування цього запису минув (48 годин)",
        )

    updated = entry.model_copy(
        update={
            "status": body.status,
            "trigger_category": body.trigger_category,
            "drinks": [] if body.status == DayStatus.sober else entry.drinks,
        }
    )
    stubs.entries[record_id] = updated
    return updated
