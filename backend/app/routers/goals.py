"""Ендпоінти особистих цілей."""

import datetime as dt

from fastapi import APIRouter, Depends, Path, Query, Request, Response

from backend.app.errors import COMMON_RESPONSES, api_error
from backend.app.models import ErrorResponse, GoalCreate, GoalList, GoalOut
from backend.app.security import CurrentUser, _db_session, get_current_user
from backend.app.services.progress_sync import recompute_progress

router = APIRouter(prefix="/goals", tags=["Goals"])

GOAL_ID = Path(..., ge=1, description="Ідентифікатор цілі.", examples=[1])
NOT_FOUND = {"model": ErrorResponse, "description": "Ціль не знайдено"}


def _goal_out(goal) -> GoalOut:
    return GoalOut(
        goal_id=goal.goal_id,
        user_id=goal.user_id,
        target_days=goal.target_days,
        is_achieved=goal.is_achieved,
        progress_days=goal.progress_days,
        created_at=goal.created_at,
    )


def _today_local() -> dt.date:
    from backend.app.core.clock import today_local

    return today_local()


@router.get(
    "",
    response_model=GoalList,
    summary="Список особистих цілей",
    description="Повертає сторінку цілей поточного користувача (FR-004, FR-005).",
    responses={**COMMON_RESPONSES},
)
def list_goals(
    db=Depends(_db_session),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(get_current_user),
):
    from backend.app.repositories.goals import list_goals_page, lock_user_for_update

    lock_user_for_update(db, user.user_id)
    items, total = list_goals_page(
        db,
        user.user_id,
        limit=limit,
        offset=offset,
    )
    recompute_progress(db, user.user_id, _today_local())
    result = GoalList(
        items=[_goal_out(goal) for goal in items],
        total=total,
        limit=limit,
        offset=offset,
    )
    db.commit()
    return result


def _get_own_goal(db, goal_id: int, user: CurrentUser):
    from backend.app.repositories.goals import get_goal

    goal = get_goal(db, user.user_id, goal_id)
    if goal is None:
        raise api_error(404, "GOAL_NOT_FOUND", f"Ціль {goal_id} не знайдено")
    return goal


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
    db=Depends(_db_session),
    user: CurrentUser = Depends(get_current_user),
):
    from backend.app.repositories.goals import create_goal as add_goal

    goal = add_goal(db, user.user_id, body.target_days)
    recompute_progress(db, user.user_id, _today_local())
    result = _goal_out(goal)
    db.commit()
    response.headers["Location"] = f"{request.url.path.rstrip('/')}/{goal.goal_id}"
    return result


@router.get(
    "/{goal_id}",
    response_model=GoalOut,
    summary="Отримати ціль",
    description="Повертає ціль поточного користувача та ознаку її досягнення (FR-004, FR-005).",
    responses={**COMMON_RESPONSES, 404: NOT_FOUND},
)
def get_goal(
    goal_id: int = GOAL_ID,
    db=Depends(_db_session),
    user: CurrentUser = Depends(get_current_user),
):
    from backend.app.repositories.goals import lock_user_for_update

    lock_user_for_update(db, user.user_id)
    goal = _get_own_goal(db, goal_id, user)
    recompute_progress(db, user.user_id, _today_local())
    result = _goal_out(goal)
    db.commit()
    return result


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
    db=Depends(_db_session),
    user: CurrentUser = Depends(get_current_user),
):
    from backend.app.repositories.goals import lock_user_for_update, update_goal

    lock_user_for_update(db, user.user_id)
    goal = _get_own_goal(db, goal_id, user)
    updated = update_goal(db, goal, body.target_days)
    recompute_progress(db, user.user_id, _today_local())
    result = _goal_out(updated)
    db.commit()
    return result


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
def delete_goal(
    goal_id: int = GOAL_ID,
    db=Depends(_db_session),
    user: CurrentUser = Depends(get_current_user),
):
    from backend.app.repositories.goals import delete_goal as remove_goal

    goal = _get_own_goal(db, goal_id, user)
    remove_goal(db, goal)
    db.commit()
    return Response(status_code=204)
