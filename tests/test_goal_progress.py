from dataclasses import dataclass

import pytest

from backend.app.services.statistics import calculate_goal_progress


@dataclass(frozen=True)
class Goal:
    goal_id: int
    target_days: int


def test_goal_progress_uses_current_streak_and_personal_targets():
    result = calculate_goal_progress(
        current_streak=6,
        longest_streak=8,
        goals=[Goal(1, 30), Goal(2, 7), Goal(3, 10)],
    )

    assert result == (True, 10, [7], 6)


def test_achieved_goal_keeps_progress_after_a_later_relapse():
    result = calculate_goal_progress(
        current_streak=0,
        longest_streak=7,
        goals=[Goal(1, 7)],
    )

    assert result == (True, None, [7], 0)


def test_duplicate_completed_targets_are_returned_once_in_order():
    result = calculate_goal_progress(
        current_streak=14,
        longest_streak=14,
        goals=[Goal(4, 14), Goal(1, 7), Goal(2, 14)],
    )

    assert result == (True, None, [7, 14], 0)


def test_goal_progress_without_goals_is_distinct_from_completed_goals():
    assert calculate_goal_progress(
        current_streak=0,
        longest_streak=0,
        goals=[],
    ) == (False, None, [], 0)


@pytest.mark.parametrize(
    ("current_streak", "longest_streak"),
    [(-1, 0), (0, -1), (2, 1)],
)
def test_goal_progress_rejects_invalid_streaks(current_streak, longest_streak):
    with pytest.raises(ValueError):
        calculate_goal_progress(
            current_streak=current_streak,
            longest_streak=longest_streak,
            goals=[Goal(1, 7)],
        )
