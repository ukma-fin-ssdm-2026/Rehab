import pytest
from pydantic import ValidationError

from backend.app.models import GoalList, GoalMilestoneOut


def test_fixed_goal_list_contains_read_only_milestones():
    result = GoalList(
        items=[
            GoalMilestoneOut(target_days=7, is_achieved=False, progress_days=3),
            GoalMilestoneOut(target_days=30, is_achieved=False, progress_days=3),
        ]
    )

    assert [item.target_days for item in result.items] == [7, 30]


@pytest.mark.parametrize("progress_days", [-1, 31])
def test_goal_milestone_rejects_invalid_progress(progress_days):
    with pytest.raises(ValidationError):
        GoalMilestoneOut(
            target_days=30,
            is_achieved=False,
            progress_days=progress_days,
        )
