import datetime
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Union

from ..client import get_client
from pyrh.urls import HISTORICALS


def get_closing_price_for_stocks(
    **stocks: Union[datetime.date, List[datetime.date]]
) -> Dict[str, float]:
    """
    Usage:
        >>> get_closing_price_for_stocks(HUBS=datetime.date(2020, 8, 21))
        {'HUBS': {datetime.date(2020, 8, 21): 284.41}}

        >>> get_closing_price_for_stocks(
        ...     HUBS=[datetime.date(2020, 8, 21), datetime.date(2020, 8, 20)]
        ... )
        {'HUBS': {datetime.date(2020, 8, 20): 287.20, datetime.date(2020, 8, 21): 284.41}}
    """
    for date in stocks.values():
        if date > datetime.date.today():
            raise ValueError('Cannot predict the future!')

        if (datetime.date.today() - date).days > 365:
            # TODO: I think this only allows to do by week? So not sure how to get this information.
            # However, this function is currently only designed to analyze options (all short term)
            # so one year should be fine.
            raise NotImplementedError

    stock_quotes = _get_raw_results(
        names=[name for name in stocks],
        time_window=Window.ONE_YEAR_DAY,
        bounds=Bounds.REGULAR,
    )

    output: Dict[str, Union[str, float]] = {
        name.upper(): date.strftime('%Y-%m-%dT00:00:00Z')
        for name, date in stocks.items()
    }
    for stock in stock_quotes:
        name = stock['symbol']
        for quote in reversed(stock['historicals']):
            if quote['begins_at'] == output[name]:
                output[name] = float(quote['close_price'])
                break

    return output


class Bounds(Enum):
    REGULAR = 1
    EXTENDED = 2


class Window(Enum):
    # TODO: Need to reverse engineer "all-time".
    FIVE_MINUTES_DAY = {'interval': '5minute', 'span': 'day'}
    FIVE_MINUTES_WEEK = {'interval': '5minute', 'span': 'week'}

    TEN_MINUTES_DAY = {'interval': '10minute', 'span': 'day'}
    TEN_MINUTES_WEEK = {'interval': '10minute', 'span': 'week'}

    ONE_YEAR_DAY = {'interval': 'day', 'span': 'year'}
    ONE_YEAR_WEEK = {'interval': 'week', 'span': 'year'}
    FIVE_YEARS = {'interval': 'week'}


def _get_raw_results(names: List[str], time_window: Window, bounds: Bounds) -> List[Dict[str, Any]]:
    """
    :returns: a list of quotes in the following format
        {
            "quote": "https://api.robinhood.com/quotes/872a4a6f-9e98-49a4-87fc-f851e0b00e8d/",
            "symbol": "HUBS",
            "interval": "day",
            "span": "year",
            "bounds": "regular",
            "instrument": "https://api.robinhood.com/instruments/872a4a6f-9e98-49a4-87fc-f851e0b00e8d/",    # noqa: E501
            "historicals": [
                {
                    "begins_at": "2019-12-23T00:00:00Z",
                    "open_price": "159.810000",
                    "close_price": "157.130000",
                    "high_price": "159.955300",
                    "low_price": "156.570000",
                    "volume": 325473,
                    "session": "reg",
                    "interpolated": false
                },
                ...
            ]
        }
    """
    return get_client().get(
        HISTORICALS,
        params={
            'symbols': ','.join(names).upper(),
            **time_window.value,
            'bounds': bounds.name.lower(),
        },
    )['results']
