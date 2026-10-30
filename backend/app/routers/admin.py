# AI-GENERATED START
"""Адмінський API (тільки роль admin): скарги, агрегати, діаграма тригерів.

Імпорти шару БД (модель User, репозиторії, годинник) відкладені до виклику,
як у security.py, щоб `app` імпортувався без підключення до БД.
"""

import datetime as dt
from typing import Literal

from fastapi import APIRouter, Depends, Query

from backend.app.errors import COMMON_RESPONSES
from backend.app.models import ErrorResponse
from backend.app.schemas.admin import TriggerDistributionOut
from backend.app.schemas.complaints import (
    AdminComplaintList,
    AdminComplaintOut,
    AdminOverview,
    ComplaintDecision,
    ComplaintOut,
)
from backend.app.security import CurrentUser, _db_session, require_role

router = APIRouter(prefix="/admin", tags=["Admin"])

ADMIN_RESPONSES = {
    **COMMON_RESPONSES,
    403: {"model": ErrorResponse, "description": "Потрібна роль admin"},
}
REPORT_DAYS = 30


COMPLAINT_RESPONSES = {
    **ADMIN_RESPONSES,
    404: {"model": ErrorResponse, "description": "Скаргу не знайдено"},
}


@router.get("/complaints", response_model=AdminComplaintList, responses=ADMIN_RESPONSES)
def list_complaints(
    status: Literal["pending", "approved", "rejected", "all"] = "pending",
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db=Depends(_db_session),
    _admin: CurrentUser = Depends(require_role("admin")),
) -> AdminComplaintList:
    """Скарги з фігурантами; глобального списку акаунтів немає."""
    from backend.app.services import complaints

    rows, total = complaints.list_complaints(db, status, limit, offset)
    return AdminComplaintList(
        items=[complaints.to_admin_out(db, row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/complaints/{complaint_id}",
    response_model=AdminComplaintOut,
    responses=COMPLAINT_RESPONSES,
)
def get_complaint(
    complaint_id: int,
    db=Depends(_db_session),
    _admin: CurrentUser = Depends(require_role("admin")),
) -> AdminComplaintOut:
    from backend.app.services import complaints

    return complaints.to_admin_out(db, complaints.get_complaint(db, complaint_id))


@router.patch(
    "/complaints/{complaint_id}",
    response_model=ComplaintOut,
    responses={
        **COMPLAINT_RESPONSES,
        409: {"model": ErrorResponse, "description": "Скаргу вже розглянуто"},
    },
)
def decide_complaint(
    complaint_id: int,
    payload: ComplaintDecision,
    db=Depends(_db_session),
    admin: CurrentUser = Depends(require_role("admin")),
) -> ComplaintOut:
    """Схвалення завершує зв'язок пари назавжди; відхилення його не відновлює."""
    from backend.app.services import complaints

    complaint = complaints.decide_complaint(
        db, complaint_id, admin.user_id, payload.decision
    )
    db.commit()
    return ComplaintOut.model_validate(complaint)


@router.get("/overview", response_model=AdminOverview, responses=ADMIN_RESPONSES)
def overview(
    db=Depends(_db_session),
    _admin: CurrentUser = Depends(require_role("admin")),
) -> AdminOverview:
    """Агрегати без персональних даних; межі днів — Europe/Kyiv."""
    from backend.app.core.clock import today_local
    from backend.app.services.complaints import admin_overview

    return admin_overview(db, today_local())


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
