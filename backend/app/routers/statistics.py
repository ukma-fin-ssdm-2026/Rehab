"""API статистики тверезості для прототипу Rehab."""

import datetime as dt
from typing import Literal

from fastapi import APIRouter, Depends, Query

from backend.app import stubs
from backend.app.errors import COMMON_RESPONSES, api_error
from backend.app.models import StatisticsOut
from backend.app.security import CurrentUser, get_current_user
from backend.app.services.statistics import calculate_statistics

router = APIRouter(prefix="/statistics", tags=["Statistics"])


@router.get(
    "",
    response_model=StatisticsOut,
    summary="Отримати статистику тверезості",
    description=(
        "Повертає кількість тверезих днів, днів із вживанням, "
        "поточну й найдовшу серії, а також прогрес цілей 7 і 30 днів. "
        "Дані обчислюються з календарних записів поточного користувача."
    ),
    responses={**COMMON_RESPONSES},
)
def get_statistics(
    period: Literal["all", "week", "month", "year"] = Query(
        "all",
        description=(
            "Період статистики: all — увесь час, "
            "week — останні 7 днів, "
            "month — поточний місяць, "
            "year — поточний рік."
        ),
    ),
    user: CurrentUser = Depends(get_current_user),
):
    """Повертає статистику для авторизованого користувача."""

    tracking_start_date = stubs.tracking_start_dates.get(user.user_id)

    if tracking_start_date is None:
        raise api_error(
            404,
            "TRACKING_NOT_STARTED",
            "Для користувача ще не встановлено дату початку відстеження",
        )

    user_entries = [
        entry for entry in stubs.entries.values() if entry.user_id == user.user_id
    ]

    result = calculate_statistics(
        tracking_start_date=tracking_start_date,
        today=dt.date.today(),
        entries=user_entries,
        goals=stubs.goals.values(),
        period=period,
    )

    return StatisticsOut(**result)
