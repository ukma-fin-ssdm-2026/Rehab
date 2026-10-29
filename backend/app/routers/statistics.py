"""API статистики тверезості."""

from typing import Literal

from fastapi import APIRouter, Depends, Query

from backend.app.errors import COMMON_RESPONSES, api_error
from backend.app.models import StatisticsOut
from backend.app.security import CurrentUser, _db_session, get_current_user
from backend.app.services.progress_sync import recompute_progress
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
    db=Depends(_db_session),
    user: CurrentUser = Depends(get_current_user),
):
    """Повертає статистику з календаря та цілей поточного користувача."""

    from backend.app.core.clock import today_local
    from backend.app.repositories.entries import list_user_entries
    from backend.app.repositories.goals import list_user_goals, lock_user_for_update

    account = lock_user_for_update(db, user.user_id)

    if account is None or account.tracking_start_date is None:
        raise api_error(
            404,
            "TRACKING_NOT_STARTED",
            "Для користувача ще не встановлено дату початку відстеження",
        )

    today = today_local()
    user_entries = list_user_entries(db, user.user_id)
    user_goals = list_user_goals(db, user.user_id)
    recompute_progress(db, user.user_id, today)

    result = calculate_statistics(
        tracking_start_date=account.tracking_start_date,
        today=today,
        entries=user_entries,
        goals=user_goals,
        period=period,
    )

    db.commit()
    return StatisticsOut(**result)
