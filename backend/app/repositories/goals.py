"""Запити до таблиці особистих цілей."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.db.models.goal import Goal


def get_goal(db: Session, user_id: int, goal_id: int) -> Goal | None:
    """Знаходить ціль лише серед цілей указаного користувача."""

    statement = select(Goal).where(
        Goal.user_id == user_id,
        Goal.goal_id == goal_id,
    )
    return db.scalar(statement)


def list_user_goals(db: Session, user_id: int) -> list[Goal]:
    """Повертає всі цілі користувача за зростанням ідентифікатора."""

    statement = (
        select(Goal)
        .where(Goal.user_id == user_id)
        .order_by(Goal.goal_id)
    )
    return list(db.scalars(statement).all())


def list_goals_page(
    db: Session,
    user_id: int,
    *,
    limit: int,
    offset: int,
) -> tuple[list[Goal], int]:
    """Повертає сторінку цілей і загальну кількість цілей користувача."""

    ownership_filter = Goal.user_id == user_id
    total = db.scalar(
        select(func.count()).select_from(Goal).where(ownership_filter)
    )
    statement = (
        select(Goal)
        .where(ownership_filter)
        .order_by(Goal.goal_id)
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement).all()), int(total or 0)


def create_goal(db: Session, user_id: int, target_days: int) -> Goal:
    """Додає ціль у поточну транзакцію та присвоює їй ідентифікатор."""

    goal = Goal(user_id=user_id, target_days=target_days, is_achieved=False)
    db.add(goal)
    db.flush()
    return goal


def update_goal(db: Session, goal: Goal, target_days: int) -> Goal:
    """Змінює число днів у цілі без завершення транзакції."""

    goal.target_days = target_days
    db.flush()
    return goal


def delete_goal(db: Session, goal: Goal) -> None:
    """Видаляє ціль у поточній транзакції."""

    db.delete(goal)
    db.flush()
