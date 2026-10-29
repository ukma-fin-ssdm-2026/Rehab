# AI-GENERATED START
"""Адмінський API (тільки роль admin): акаунти, блокування, діаграма тригерів.

Імпорти шару БД (модель User, репозиторії, годинник) відкладені до виклику,
як у security.py, щоб `app` імпортувався без підключення до БД.
"""

import datetime as dt

from fastapi import APIRouter, Depends, Query

from backend.app.errors import COMMON_RESPONSES, api_error
from backend.app.models import ErrorResponse
from backend.app.schemas.admin import (
    AdminUserList,
    AdminUserOut,
    BlockRequest,
    TriggerDistributionOut,
)
from backend.app.security import CurrentUser, _db_session, require_role

router = APIRouter(prefix="/admin", tags=["Admin"])

ADMIN_RESPONSES = {
    **COMMON_RESPONSES,
    403: {"model": ErrorResponse, "description": "Потрібна роль admin"},
}
REPORT_DAYS = 30


@router.get("/users", response_model=AdminUserList, responses=ADMIN_RESPONSES)
def list_users(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db=Depends(_db_session),
    _admin: CurrentUser = Depends(require_role("admin")),
) -> AdminUserList:
    """Сторінка акаунтів без хешів паролів і службових полів."""
    from sqlalchemy import func, select

    from backend.app.db.models.user import User

    total = db.scalar(select(func.count()).select_from(User)) or 0
    rows = db.scalars(
        select(User).order_by(User.user_id).limit(limit).offset(offset)
    ).all()
    return AdminUserList(
        items=[AdminUserOut.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/users/{user_id}/block",
    response_model=AdminUserOut,
    responses={
        **ADMIN_RESPONSES,
        404: {"model": ErrorResponse, "description": "Акаунт не знайдено"},
    },
)
def block_user(
    user_id: int,
    payload: BlockRequest,
    db=Depends(_db_session),
    admin: CurrentUser = Depends(require_role("admin")),
) -> AdminUserOut:
    """Блокує або розблокує акаунт. Розблокування не оживляє старі токени."""
    from backend.app.repositories.users import get_user, set_blocked

    target = get_user(db, user_id)
    if target is None:
        raise api_error(404, "USER_NOT_FOUND", "Акаунт не знайдено")
    if payload.is_blocked and (
        target.user_id == admin.user_id or target.role == "admin"
    ):
        raise api_error(
            403, "ADMIN_BLOCK_NOT_ALLOWED", "Адміністратора блокувати не можна"
        )
    # Повторне встановлення поточного стану не помилка й не чіпає token_version.
    if target.is_blocked != payload.is_blocked:
        target = set_blocked(db, user_id, payload.is_blocked)
        db.commit()
    return AdminUserOut.model_validate(target)


@router.get(
    "/trigger-distribution",
    response_model=TriggerDistributionOut,
    responses=ADMIN_RESPONSES,
)
def trigger_distribution(
    db=Depends(_db_session),
    _admin: CurrentUser = Depends(require_role("admin")),
) -> TriggerDistributionOut:
    """Анонімний розподіл тригерів зривів за останні 30 днів усіх акаунтів."""
    from backend.app.core.clock import today_local
    from backend.app.repositories.entries import list_relapse_entries
    from backend.app.services.statistics import calculate_trigger_distribution

    # calculate_trigger_distribution порівнює з dt.date.today() хоста, тож
    # між 00:00 і 03:00 за Києвом today_local() може бути "завтра" для сервера.
    today = min(today_local(), dt.date.today())
    entries = list_relapse_entries(
        db, today - dt.timedelta(days=REPORT_DAYS - 1), today
    )
    return TriggerDistributionOut(
        **calculate_trigger_distribution(entries, today=today)
    )


# AI-GENERATED END
