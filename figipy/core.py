import dataclasses
import json
import os
from enum import Enum
from logging import getLogger
from typing import List, Iterable

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from figipy import (
    RateLimitError,
    PayloadTooLargeError,
    AuthenticationError,
    NumberRange,
    DateRange,
    assert_data_range_is_valid,
    convert_date_range_to_string,
    convert_number_range_to_string,
)

logger = getLogger(__name__)

OPEN_FIGI_DEFAULT_URL = "https://api.openfigi.com"


class MappingValues(Enum):
    ID_TYPE = "idType"
    EXCHANGE_CODE = "exchCode"
    MIC_CODE = "micCode"
    CURRENCY = "currency"
    MARKET_SECTOR_DESCRIPTION = "marketSecDes"
    SECURITY_TYPE = "securityType"
    SECURITY_TYPE_2 = "securityType2"
    STATE_CODE = "stateCode"


@dataclasses.dataclass()
class OpenApiFIGIResponse:
    error: str


@dataclasses.dataclass()
class OpenFIGIObject:
    figi: str
    security_type: str = None
    security_type_2: str = None
    market_sector: str = None
    exchange_code: str = None
    ticker: str = None
    name: str = None
    id: str = None
    share_class_figi: str = None
    composite_figi: str = None
    security_description: str = None
    future_or_option_id: str = None
    metadata: dict = None

    @classmethod
    def from_figi_data(cls, data: dict) -> "OpenFIGIObject":
        return OpenFIGIObject(
            figi=data.get("figipy"),
            security_type=data.get("securityType"),
            security_type_2=data.get("securityType2"),
            market_sector=data.get("marketSecDes"),
            exchange_code=data.get("exchCode"),
            name=data.get("name"),
            id=data.get("id"),
            share_class_figi=data.get("shareClassFIGI"),
            composite_figi=data.get("compositeFIGI"),
            security_description=data.get("securityDescription"),
            future_or_option_id=data.get("uniqueIDFutOpt"),
        )


@dataclasses.dataclass()
class OpenFIGIProperties:
    exchange_code: str = None
    mic_code: str = None
    currency: str = None
    market_sector_description: str = None
    security_type: str = None
    security_type_2: str = None
    include_unlisted_equities: bool = None
    option_type: str = None
    strike: NumberRange = None
    contract_size: NumberRange = None
    coupon: NumberRange = None
    expiration: DateRange = None
    maturity: DateRange = None
    state_code: str = None

    def __post_init__(self):
        if self.expiration:
            assert self.security_type_2 in (
                "Option",
                "Warrant",
            )
            assert_data_range_is_valid(self.expiration)
        if self.maturity:
            assert self.security_type_2 in ("Pool",)
            assert_data_range_is_valid(self.maturity)

    def as_filter(self) -> dict:
        return {
            key: value
            for (key, value) in {
                "exchCode": self.exchange_code,
                "micCode": self.mic_code,
                "currency": self.currency,
                "marketSecDes": self.market_sector_description,
                "securityType": self.security_type,
                "securityType2": self.security_type_2,
                "includeUnlistedEquities": self.include_unlisted_equities,
                "optionType": self.option_type,
                "strike": convert_number_range_to_string(self.strike),
                "contractSize": convert_number_range_to_string(self.contract_size),
                "coupon": convert_number_range_to_string(self.coupon),
                "expiration": convert_date_range_to_string(self.expiration),
                "maturity": convert_date_range_to_string(self.maturity),
                "stateCode": self.state_code,
            }.items()
            if value is not None
        }


class OpenFIGIApi:
    API_KEY = os.environ.get("OPEN_FIGI_API_KEY")
    API_URL = os.environ.get("OPEN_FIGI_API_URL", OPEN_FIGI_DEFAULT_URL)
    API_RAISE_ON_ERROR = json.loads(os.environ.get("OPEN_FIGI_RAISE_ON_ERROR", "false"))
    API_RETRY_COUNT = int(os.environ.get("OPEN_FIGI_API_RETRY_COUNT", 2))

    def __init__(
        self, raise_on_error=None, api_key=None, api_url=None, api_retry_count=None
    ):
        self.raise_on_error = raise_on_error or self.API_RAISE_ON_ERROR
        self.api_retry_count = api_retry_count or self.API_RETRY_COUNT
        self.api_key = api_key or self.API_KEY
        self.api_url = api_url or self.API_URL

    def create_session(self) -> requests.Session:
        session = requests.Session()
        session.mount(
            "https://",
            HTTPAdapter(
                max_retries=Retry(
                    total=self.api_retry_count,
                    backoff_factor=5,
                    status_forcelist=[429],
                    method_whitelist=False,
                )
            ),
        )
        return session

    def _perform_pagination_request(
        self, url: str, method: str, data=None
    ) -> Iterable[dict]:
        session = self.create_session()
        response = self._perform_request(
            url,
            method,
            data=data,
            session=session
        )
        while "data" in response and len(response["data"]):
            for part in response["data"]:
                yield part
            if "next" in response:
                response = self._perform_request(
                    url,
                    method,
                    data=dict(data, start=response["next"]),
                    session=session
                )
            else:
                break

    def _perform_request(self, url: str, method: str, data=None, session=None) -> dict:
        if session is None:
            session = self.create_session()
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["X-OPENFIGI-APIKEY"] = self.api_key
        response = session.request(
            method,
            url,
            data=json.dumps(data),
            headers=headers
        )
        if response.status_code == 429:
            logger.warning(
                "Your application is being rate-limited, try to perform fewer requests"
            )
            if self.raise_on_error:
                raise RateLimitError()
        if response.status_code == 413:
            logger.warning(
                "Your application requested too large of a payload, you may want to supply an API key"
            )
            if self.raise_on_error:
                raise PayloadTooLargeError()
        if response.status_code == 403:
            logger.error(
                f"Your API key starting with {self.api_key[:4] if self.api_key else '(NOT SUPPLIED)'} is not valid"
            )
            if self.raise_on_error:
                raise AuthenticationError()
        if self.raise_on_error:
            response.raise_for_status()
        if response.ok:
            return response.json()
        return {}

    def search(
        self, query, properties: OpenFIGIProperties = None
    ) -> Iterable[OpenApiFIGIResponse]:
        """

        :param query: Key words to query
        :param properties: Properties to filter on
        :return:
        """
        if properties is None:
            properties = OpenFIGIProperties()
        for figi_object_data in self._perform_pagination_request(
            f"{self.api_url}/v2/search/",
            "POST",
            dict(properties.as_filter(), query=query),
        ):
            yield OpenFIGIObject.from_figi_data(figi_object_data)

    def mapping_values(self, values: MappingValues) -> List[str]:
        """

        :param values: The name of the Mapping Job property for which to list the possible values.
        :return: The current list of values present for the property named by the key request parameter.
        """
        if values is None:
            raise ValueError("Supplied value may not be None")
        return self._perform_request(
            f"{self.api_url}/v2/mapping/values/{values.value}", "GET"
        )["values"]
