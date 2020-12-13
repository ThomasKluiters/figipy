import datetime
import pytest

from figipy import OpenFIGIProperties


@pytest.mark.parametrize(
    ("property_object", "expected_filter"),
    [
        (OpenFIGIProperties(exchange_code="NYSE"), {"exchCode": "NYSE"}),
        (OpenFIGIProperties(mic_code="A2XX"), {"micCode": "A2XX"}),
        (OpenFIGIProperties(currency="USD"), {"currency": "USD"}),
        (
            OpenFIGIProperties(market_sector_description="Equity"),
            {"marketSecDes": "Equity"},
        ),
        (
            OpenFIGIProperties(security_type="Financial index option."),
            {"securityType": "Financial index option."},
        ),
        (OpenFIGIProperties(security_type_2="Option"), {"securityType2": "Option"}),
        (
            OpenFIGIProperties(include_unlisted_equities=True),
            {"includeUnlistedEquities": True},
        ),
        (OpenFIGIProperties(option_type="Call"), {"optionType": "Call"}),
        (OpenFIGIProperties(strike=(2, 3)), {"strike": [2, 3]}),
        (OpenFIGIProperties(contract_size=(100, None)), {"contractSize": [100, None]}),
        (OpenFIGIProperties(coupon=(100, 100)), {"coupon": [100, 100]}),
        (
            OpenFIGIProperties(
                security_type_2="Option", expiration=(datetime.date(2020, 12, 11), None)
            ),
            {"securityType2": "Option", "expiration": ["2020-12-11", "2021-12-10"]},
        ),
        (
            OpenFIGIProperties(
                security_type_2="Pool", maturity=(None, datetime.date(2020, 12, 11))
            ),
            {"securityType2": "Pool", "maturity": ["2019-12-13", "2020-12-11"]},
        ),
        (OpenFIGIProperties(state_code="NY"), {"stateCode": "NY"}),
        (OpenFIGIProperties(), {}),
    ],
)
def test_properties_propagated_when_calling_filter(property_object, expected_filter):
    assert property_object.as_filter() == expected_filter
