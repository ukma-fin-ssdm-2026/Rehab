"""Read-only API для фіксованих етапів тверезості."""

from fastapi import APIRouter, Depends

from backend.app.errors import COMMON_RESPONSES, api_error
from backend.app.models import GoalList, GoalMilestoneOut
from backend.app.security import CurrentUser, _db_session, get_current_user
from backend.app.services.statistics import FIXED_GOAL_DAYS, calculate_statistics

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.get(
    "",
    response_model=GoalList,
    summary="Отримати фіксовані етапи тверезості",
    description="Повертає етапи 7 і 30 днів та їхній прогрес для поточного користувача.",
    responses={**COMMON_RESPONSES},
)
def list_goals(
    db=Depends(_db_session),
    user: CurrentUser = Depends(get_current_user),
):
    from backend.app.core.clock import today_local
    from backend.app.repositories.entries import list_user_entries
    from backend.app.repositories.users import get_user

    account = get_user(db, user.user_id)
    if account is None or account.tracking_start_date is None:
        raise api_error(
            404,
            "TRACKING_NOT_STARTED",
            "Для користувача ще не встановлено дату початку відстеження",
        )

    statistics = calculate_statistics(
        tracking_start_date=account.tracking_start_date,
        today=today_local(),
        entries=list_user_entries(db, user.user_id),
    )
    current_streak = statistics["current_streak"]
    completed_goal_days = statistics["completed_goal_days"]

    return GoalList(
        items=[
            GoalMilestoneOut(
                target_days=target_days,
                is_achieved=target_days in completed_goal_days,
                progress_days=(
                    target_days
                    if target_days in completed_goal_days
                    else min(current_streak, target_days)
                ),
            )
            for target_days in FIXED_GOAL_DAYS
        ]
    )
