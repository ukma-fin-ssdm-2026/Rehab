import datetime as dt

import pytest
from pydantic import ValidationError

from backend.app.models import GoalCreate, GoalOut


@pytest.mark.parametrize("target_days", [1, 10, 3650])
def test_goal_create_accepts_supported_targets(target_days):
    assert GoalCreate.model_validate({"target_days": target_days}).target_days == target_days


@pytest.mark.parametrize("target_days", [0, 3651, True, 10.5, "10"])
def test_goal_create_rejects_non_integer_or_out_of_range_targets(target_days):
    with pytest.raises(ValidationError):
        GoalCreate.model_validate({"target_days": target_days})


@pytest.mark.parametrize("field", ["user_id", "is_achieved"])
def test_goal_create_rejects_server_owned_fields(field):
    with pytest.raises(ValidationError):
        GoalCreate.model_validate({"target_days": 10, field: 42})


def test_goal_out_contains_creation_time_and_progress():
    goal = GoalOut(
        goal_id=1,
        user_id=42,
        target_days=10,
        is_achieved=False,
        progress_days=6,
        created_at=dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc),
    )

    assert goal.progress_days == 6
    assert goal.created_at == dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)
