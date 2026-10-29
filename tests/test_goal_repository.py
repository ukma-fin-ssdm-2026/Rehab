import importlib
import os
import sys
import types

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session


@pytest.fixture
def orm_modules():
    base_name = "backend.app.db.base"
    used_test_base = False

    if base_name not in sys.modules:
        try:
            importlib.import_module(base_name)
            used_test_base = False
        except ModuleNotFoundError as error:
            if error.name != base_name:
                raise
            base_module = types.ModuleType(base_name)

            class TestBase(DeclarativeBase):
                pass

            base_module.Base = TestBase
            sys.modules[base_name] = base_module

    user_module = importlib.import_module("backend.app.db.models.user")
    goal_module = importlib.import_module("backend.app.db.models.goal")
    repository = importlib.import_module("backend.app.repositories.goals")

    yield user_module.User, goal_module.Goal, repository

    if used_test_base:
        for module_name in (
            "backend.app.repositories.goals",
            "backend.app.db.models.goal",
            "backend.app.db.models.user",
        ):
            sys.modules.pop(module_name, None)
        sys.modules.pop(base_name, None)


@pytest.fixture
def goal_session(orm_modules):
    User, Goal, _ = orm_modules
    database_url = os.getenv("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    engine = create_engine(database_url)
    Base = User.__bases__[0]
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session, User, Goal
        session.rollback()
    Base.metadata.drop_all(engine)
    engine.dispose()


def add_user(session, User, *, email, user_id=None):
    user = User(
        user_id=user_id,
        email=email,
        name="Test User",
        nickname=email.split("@")[0],
        password_hash="test-hash",
        tracking_start_date=__import__("datetime").date(2026, 10, 1),
    )
    session.add(user)
    session.flush()
    return user


def test_goal_repository_scopes_orders_and_paginates(goal_session, orm_modules):
    session, User, _ = goal_session
    _, _, repository = orm_modules
    owner = add_user(session, User, email="owner@example.test")
    other = add_user(session, User, email="other@example.test")

    first = repository.create_goal(session, owner.user_id, 7)
    second = repository.create_goal(session, owner.user_id, 10)
    repository.create_goal(session, other.user_id, 30)

    assert repository.get_goal(session, owner.user_id, first.goal_id) is first
    assert repository.get_goal(session, other.user_id, first.goal_id) is None
    assert [goal.goal_id for goal in repository.list_user_goals(session, owner.user_id)] == [
        first.goal_id,
        second.goal_id,
    ]

    items, total = repository.list_goals_page(
        session,
        owner.user_id,
        limit=1,
        offset=1,
    )
    assert total == 2
    assert [goal.goal_id for goal in items] == [second.goal_id]


def test_goal_repository_updates_and_deletes_without_committing(
    goal_session, orm_modules
):
    session, User, _ = goal_session
    _, _, repository = orm_modules
    owner = add_user(session, User, email="owner@example.test")
    goal = repository.create_goal(session, owner.user_id, 7)
    goal.is_achieved = True
    created_at = goal.created_at

    updated = repository.update_goal(session, goal, 10)

    assert updated.target_days == 10
    assert updated.created_at == created_at
    assert updated.is_achieved is True
    assert session.in_transaction()

    repository.delete_goal(session, updated)
    assert repository.get_goal(session, owner.user_id, goal.goal_id) is None


def test_goal_repository_enforces_target_range_in_database(goal_session):
    session, User, Goal = goal_session
    from sqlalchemy.exc import IntegrityError

    owner = add_user(session, User, email="owner@example.test")
    session.add(Goal(user_id=owner.user_id, target_days=0, is_achieved=False))

    with pytest.raises(IntegrityError):
        session.flush()

    session.rollback()

