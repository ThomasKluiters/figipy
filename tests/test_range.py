import pytest
import datetime

from figipy import assert_data_range_is_valid, convert_date_range_to_string


@pytest.mark.parametrize(
    ("data_range", "expected_to_succeed"),
    [
        ((None, None), False),
        ((3, 5), True),
        ((None, 5), True),
        ((2, None), True),
        ((datetime.date(2020, 11, 12), None), True),
        ((None, datetime.date(2020, 11, 12)), True),
        ((datetime.date(2020, 11, 12), datetime.date(2020, 11, 12)), True),
        ((datetime.date(2020, 12, 12), datetime.date(2020, 11, 12)), False),
    ],
)
def test_data_range_assertion(data_range, expected_to_succeed):
    if not expected_to_succeed:
        with pytest.raises(AssertionError):
            assert_data_range_is_valid(data_range)
    else:
        assert_data_range_is_valid(data_range)


@pytest.mark.parametrize(
    ("date_range", "expected_date_range_string"),
    [
        ((datetime.date(2020, 11, 12), None), ["2020-11-12", "2021-11-11"]),
        ((None, datetime.date(2020, 11, 12)), ["2019-11-14", "2020-11-12"]),
        (
            (datetime.date(2020, 11, 12), datetime.date(2020, 11, 12)),
            ["2020-11-12", "2020-11-12"],
        ),
        (None, None),
    ],
)
def test_date_range_to_string(date_range, expected_date_range_string):
    assert convert_date_range_to_string(date_range) == expected_date_range_string
