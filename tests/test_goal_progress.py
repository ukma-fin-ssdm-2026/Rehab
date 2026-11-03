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


def test_all_fixed_goals_are_completed_only_after_longest_reaches_365():
    assert calculate_goal_progress(current_streak=0, longest_streak=365) == (
        True,
        None,
        [7, 30, 90, 180, 365],
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


@pytest.mark.parametrize("target", [7, 30, 90, 180, 365])
def test_five_milestone_boundaries_and_historical_badges(target):
    targets = [7, 30, 90, 180, 365]
    for streak in (target - 1, target, target + 1):
        _, active, completed, progress = calculate_goal_progress(
            current_streak=streak, longest_streak=streak
        )
        assert completed == [day for day in targets if day <= streak]
        assert active == next((day for day in targets if day > streak), None)
        assert progress == (min(streak, active) if active else 0)
    _, active, completed, progress = calculate_goal_progress(
        current_streak=0, longest_streak=target
    )
    assert target in completed
    assert active == next((day for day in targets if day > target), None)
    assert progress == 0
