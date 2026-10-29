"""Перевірки репозиторію цілей на спільній мігрованій PostgreSQL-БД."""

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.db.models.goal import Goal
from backend.app.repositories import goals


def test_goal_repository_scopes_orders_and_paginates(calendar_db, db_users):
    owner_id, other_id = db_users

    first = goals.create_goal(calendar_db, owner_id, 7)
    second = goals.create_goal(calendar_db, owner_id, 10)
    goals.create_goal(calendar_db, other_id, 30)
    calendar_db.commit()

    assert goals.get_goal(calendar_db, owner_id, first.goal_id) is not None
    assert goals.get_goal(calendar_db, other_id, first.goal_id) is None
    assert [item.goal_id for item in goals.list_user_goals(calendar_db, owner_id)] == [
        first.goal_id,
        second.goal_id,
    ]

    items, total = goals.list_goals_page(
        calendar_db,
        owner_id,
        limit=1,
        offset=1,
    )
    assert total == 2
    assert [item.goal_id for item in items] == [second.goal_id]


def test_goal_repository_updates_and_deletes_without_committing(calendar_db, db_users):
    owner_id, _ = db_users
    goal = goals.create_goal(calendar_db, owner_id, 7)
    goal.is_achieved = True
    created_at = goal.created_at

    updated = goals.update_goal(calendar_db, goal, 10)

    assert updated.target_days == 10
    assert updated.created_at == created_at
    assert updated.is_achieved is True
    assert calendar_db.in_transaction()

    goals.delete_goal(calendar_db, updated)
    assert goals.get_goal(calendar_db, owner_id, goal.goal_id) is None
    calendar_db.rollback()


def test_goal_repository_enforces_target_range_in_database(calendar_db, db_users):
    owner_id, _ = db_users
    calendar_db.add(Goal(user_id=owner_id, target_days=0, is_achieved=False))

    with pytest.raises(IntegrityError):
        calendar_db.flush()

    calendar_db.rollback()
