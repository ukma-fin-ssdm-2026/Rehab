from copy import deepcopy

import pytest

from backend.app.services.drink_summary import (
    total_volume_ml,
    volume_by_type_ml,
)


def test_total_volume_of_multiple_drinks():
    drinks = [
        {"type": "beer", "volume_ml": 330},
        {"type": "wine", "volume_ml": 150},
    ]

    result = total_volume_ml(drinks)

    assert result == 480


def test_volume_is_grouped_by_drink_type():
    drinks = [
        {"type": "beer", "volume_ml": 330},
        {"type": "wine", "volume_ml": 150},
        {"type": "beer", "volume_ml": 500},
    ]

    result = volume_by_type_ml(drinks)

    assert result == {
        "beer": 830,
        "wine": 150,
    }


@pytest.mark.parametrize(
    ("drinks", "expected"),
    [
        ([], {}),
        ([{"type": "інше", "volume_ml": 0}], {"інше": 0}),
        (
            [
                {"type": "вино", "volume_ml": 150},
                {"type": "пиво", "volume_ml": 330},
                {"type": "вино", "volume_ml": 50},
            ],
            {"вино": 200, "пиво": 330},
        ),
    ],
)
def test_grouping_preserves_empty_zero_and_arbitrary_types(drinks, expected):
    result = volume_by_type_ml(drinks)

    assert type(result) is dict
    assert result == expected
    assert list(result) == list(expected)


def test_grouping_consumes_a_single_pass_iterable():
    drinks = (
        {"type": name, "volume_ml": volume}
        for name, volume in [("beer", 330), ("wine", 150), ("beer", 500)]
    )

    assert volume_by_type_ml(drinks) == {"beer": 830, "wine": 150}
    assert list(drinks) == []


def test_summary_does_not_modify_input():
    drinks = [
        {"type": "beer", "volume_ml": 330},
        {"type": "beer", "volume_ml": 500},
    ]
    original = deepcopy(drinks)

    assert total_volume_ml(drinks) == 830
    assert volume_by_type_ml(drinks) == {"beer": 830}
    assert drinks == original


@pytest.mark.parametrize("volumes", [[], [0], [330, 150, 500]])
def test_total_accepts_a_single_pass_iterable(volumes):
    drinks = ({"type": "other", "volume_ml": volume} for volume in volumes)

    assert total_volume_ml(drinks) == sum(volumes)
    assert list(drinks) == []
