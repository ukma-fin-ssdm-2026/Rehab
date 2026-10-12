"""Ендпоінти цілей (ресурс Goal)."""

from fastapi import APIRouter, Depends, Path, Request, Response

from src.api import stubs
from src.api.errors import COMMON_RESPONSES, api_error
from src.api.models import ErrorResponse, GoalCreate, GoalOut
from src.api.security import CurrentUser, get_current_user

router = APIRouter(prefix="/goals", tags=["Goals"])

GOAL_ID = Path(..., ge=1, description="Ідентифікатор цілі.", examples=[1])
NOT_FOUND = {"model": ErrorResponse, "description": "Ціль не знайдено"}


def _get_own_goal(goal_id: int, user: CurrentUser) -> GoalOut:
    goal = stubs.goals.get(goal_id)
    if goal is None or goal.user_id != user.user_id:
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
    user: CurrentUser = Depends(get_current_user),
):
    goal = GoalOut(
        goal_id=stubs.next_goal_id(),
        user_id=user.user_id,
        target_days=body.target_days,
        is_achieved=False,
    )
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
