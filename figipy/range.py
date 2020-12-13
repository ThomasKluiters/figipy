import datetime
from typing import Optional, Tuple, Union, List

__all__ = [
    "NumberRange",
    "DateRange",
    "convert_date_range_to_string",
    "convert_number_range_to_string",
    "assert_data_range_is_valid",
]

DATE_FORMAT = "%Y-%m-%d"

NumberRange = Tuple[Optional[float], Optional[float]]
DateRange = Tuple[Optional[datetime.date], Optional[datetime.date]]


def convert_date_range_to_string(date_range: Optional[DateRange]) -> List[str]:
    if date_range is None:
        return None
    first, second = date_range
    year_offset = datetime.timedelta(weeks=52)
    first, second = first or second - year_offset, second or first + year_offset
    return [first.strftime(DATE_FORMAT), second.strftime(DATE_FORMAT)]


def convert_number_range_to_string(
    number_range: Optional[NumberRange],
) -> List[float]:
    if number_range is None:
        return None
    first, second = number_range
    first, second = first or None, second or None
    return [first, second]


def assert_data_range_is_valid(data_range: Union[NumberRange, DateRange]):
    assert len(data_range) == 2
    assert any(data_range)

    if all(data_range):
        start, end = data_range
        assert end >= start
