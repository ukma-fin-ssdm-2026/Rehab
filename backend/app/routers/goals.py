"""Ендпоінти цілей (ресурс Goal)."""

import datetime as dt

from fastapi import APIRouter, Depends, Path, Query, Request, Response

from backend.app import stubs
from backend.app.errors import COMMON_RESPONSES, api_error
from backend.app.models import DayStatus, ErrorResponse, GoalCreate, GoalList, GoalOut
from backend.app.security import CurrentUser, get_current_user
from backend.app.services.statistics import calculate_single_goal_progress, count_streaks

router = APIRouter(prefix="/goals", tags=["Goals"])

GOAL_ID = Path(..., ge=1, description="Ідентифікатор цілі.", examples=[1])
NOT_FOUND = {"model": ErrorResponse, "description": "Ціль не знайдено"}


def _user_streaks(user_id: int) -> tuple[int, int]:
    tracking_start_date = stubs.tracking_start_dates.get(user_id)
    if tracking_start_date is None:
        return 0, 0

    today = dt.date.today()
    relapse_dates = {
        entry.date
        for entry in stubs.entries.values()
        if (
            entry.user_id == user_id
            and entry.status == DayStatus.relapse
            and tracking_start_date <= entry.date <= today
        )
    }
    return count_streaks(
        start_date=tracking_start_date,
        end_date=today,
        relapse_dates=relapse_dates,
    )


def _goal_with_progress(goal: GoalOut, user_id: int) -> GoalOut:
    current_streak, longest_streak = _user_streaks(user_id)
    is_achieved, progress_days = calculate_single_goal_progress(
        current_streak=current_streak,
        longest_streak=longest_streak,
        target_days=goal.target_days,
    )
    return goal.model_copy(
        update={"is_achieved": is_achieved, "progress_days": progress_days}
    )


@router.get(
    "",
    response_model=GoalList,
    summary="Список особистих цілей",
    description="Повертає сторінку цілей поточного користувача (FR-004, FR-005).",
    responses={**COMMON_RESPONSES},
)
def list_goals(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(get_current_user),
):
    user_goals = sorted(
        (
            _goal_with_progress(goal, user.user_id)
            for goal in stubs.goals.values()
            if goal.user_id == user.user_id
        ),
        key=lambda goal: goal.goal_id,
    )
    return GoalList(
        items=user_goals[offset : offset + limit],
        total=len(user_goals),
        limit=limit,
        offset=offset,
    )


def _get_own_goal(goal_id: int, user: CurrentUser) -> GoalOut:
    goal = stubs.goals.get(goal_id)
    if goal is None or goal.user_id != user.user_id:
        raise api_error(404, "GOAL_NOT_FOUND", f"Ціль {goal_id} не знайдено")
    return _goal_with_progress(goal, user.user_id)


@router.post(
    "",
    status_code=201,
    response_model=GoalOut,
    summary="Створити ціль",
    description=(
        "Створює нову ціль тверезості (кількість днів від 1 до 3650). "
        "Нова ціль завжди створюється з `is_achieved=false` (FR-004)."
    ),
    responses={
        **COMMON_RESPONSES,
        201: {
            "description": "Ціль створено",
            "headers": {
                "Location": {
                    "description": "URL створеної цілі",
                    "schema": {"type": "string"},
                }
            },
        },
    },
)
def create_goal(
    body: GoalCreate,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
):
    goal = GoalOut(
        goal_id=stubs.next_goal_id(),
        user_id=user.user_id,
        target_days=body.target_days,
        is_achieved=False,
    )
    goal = _goal_with_progress(goal, user.user_id)
    stubs.goals[goal.goal_id] = goal
    response.headers["Location"] = f"{request.url.path.rstrip('/')}/{goal.goal_id}"
    return goal


@router.get(
    "/{goal_id}",
    response_model=GoalOut,
    summary="Отримати ціль",
    description="Повертає ціль поточного користувача та ознаку її досягнення (FR-004, FR-005).",
    responses={**COMMON_RESPONSES, 404: NOT_FOUND},
)
def get_goal(goal_id: int = GOAL_ID, user: CurrentUser = Depends(get_current_user)):
    return _get_own_goal(goal_id, user)


@router.put(
    "/{goal_id}",
    response_model=GoalOut,
    summary="Замінити ціль",
    description=(
        "Повністю замінює цільову кількість днів. Ознака `is_achieved` "
        "керується системою (FR-005) і через цей ендпоінт не змінюється."
    ),
    responses={**COMMON_RESPONSES, 404: NOT_FOUND},
)
def replace_goal(
    body: GoalCreate,
    goal_id: int = GOAL_ID,
    user: CurrentUser = Depends(get_current_user),
):
    goal = _get_own_goal(goal_id, user)
    updated = goal.model_copy(update={"target_days": body.target_days})
    updated = _goal_with_progress(updated, user.user_id)
    stubs.goals[goal_id] = updated
    return updated


@router.delete(
    "/{goal_id}",
    status_code=204,
    summary="Видалити ціль",
    description="Видаляє ціль поточного користувача. Відповідь без тіла.",
    responses={
        **COMMON_RESPONSES,
        204: {"description": "Ціль видалено"},
        404: NOT_FOUND,
    },
)
def delete_goal(goal_id: int = GOAL_ID, user: CurrentUser = Depends(get_current_user)):
    _get_own_goal(goal_id, user)
    del stubs.goals[goal_id]
    return Response(status_code=204)
