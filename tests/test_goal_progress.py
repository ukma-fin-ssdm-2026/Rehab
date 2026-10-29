import pytest

from backend.app.services.statistics import calculate_goal_progress


def test_new_user_starts_with_first_fixed_goal():
    assert calculate_goal_progress(current_streak=0, longest_streak=0) == (
        True,
        7,
        [],
        0,
    )


def test_progress_uses_current_streak_and_fixed_targets():
    assert calculate_goal_progress(current_streak=6, longest_streak=8) == (
        True,
        30,
        [7],
        6,
    )


def test_historical_milestone_stays_completed_after_relapse():
    assert calculate_goal_progress(current_streak=0, longest_streak=7) == (
        True,
        30,
        [7],
        0,
    )


def test_all_fixed_goals_are_completed_only_after_longest_reaches_30():
    assert calculate_goal_progress(current_streak=0, longest_streak=30) == (
        True,
        None,
        [7, 30],
        0,
    )


@pytest.mark.parametrize(
    ("current_streak", "longest_streak"),
    [(-1, 0), (0, -1), (2, 1)],
)
def test_goal_progress_rejects_invalid_streaks(current_streak, longest_streak):
    with pytest.raises(ValueError):
        calculate_goal_progress(
            current_streak=current_streak,
            longest_streak=longest_streak,
        )
