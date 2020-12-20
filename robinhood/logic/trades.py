import datetime
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional

from ..client import get_client
from ..models.stock import StockTrade
from ..util import get_paginated_results
from .database.stock_trade import StockTradeDBLogic
from pyrh.urls import ORDERS_BASE


def get_stock_orders(
    ticker: Optional[str] = None,
    from_date: Optional[datetime.date] = None,
    to_date: Optional[datetime.date] = None,
) -> List[StockTrade]:
    """
    :param ticker: optional filter by ticker
    :param from_date: optional filter by date. if not provided, will default to all time.
    :param to_date: optional filter by date. if not provided, will default to today.
    """
    if not to_date:
        to_date = datetime.date.today()

    logic = StockTradeDBLogic()

    # First, make sure your data is up-to-date.
    last_known_trade_date = logic.get_last_known_trade_date()
    if not last_known_trade_date or last_known_trade_date.date() < to_date:
        parameters = {}
        if last_known_trade_date:
            # Smaller pages, since we only need to get the diff.
            parameters['page_size'] = 10

        for order in _get_raw_stock_orders(params=parameters):
            state = order['state']
            if state != 'filled':
                # Ignore cancelled orders
                continue

            item = logic.create_from_raw_payload(order)
            if item.date < last_known_trade_date:
                break

    # Then, get results.
    query = logic.filter_trades_between_dates(from_date, to_date)
    if ticker:
        query = query.filter(StockTrade.name == ticker)

    return query.all()


def _get_raw_stock_orders(**kwargs: Any) -> Generator[Dict[str, Any], None, None]:
    """
    :returns: a list of trades in the following format
    {
        "id": "<UUID4>",
        "ref_id": "<UUID4>",
        "url": "https://api.robinhood.com/orders/<UUID4>/",
        "account": "https://api.robinhood.com/accounts/<accountID>/",
        "position": "https://api.robinhood.com/positions/<accountID>/8f6e5846-e6e3-4452-a1a2-5a46a630bd73/",    # noqa: E501
        "cancel": null,
        "instrument": "https://api.robinhood.com/instruments/8f6e5846-e6e3-4452-a1a2-5a46a630bd73/",
        "cumulative_quantity": "34.00000000",
        "average_price": "45.22260000",
        "fees": "0.04",
        "state": "filled",
        "type": "limit",
        "side": "sell",
        "time_in_force": "gfd",
        "trigger": "immediate",
        "price": "45.15000000",
        "stop_price": null,
        "quantity": "34.00000000",
        "reject_reason": null,
        "created_at": "2020-11-20T15:28:20.539034Z",
        "updated_at": "2020-11-20T15:28:21.157159Z",
        "last_transaction_at": "2020-11-20T15:28:20.706000Z",
        "executions": [
            {
                "price": "45.22260000",
                "quantity": "34.00000000",
                "settlement_date": "2020-11-24",
                "timestamp": "2020-11-20T15:28:20.706000Z",
                "id": "ba967f1a-4452-4264-a186-cd982b4d7042"
            }
        ],
        "extended_hours": true,
        "override_dtbp_checks": false,
        "override_day_trade_checks": false,
        "response_category": null,
        "stop_triggered_at": null,
        "last_trail_price": null,
        "last_trail_price_updated_at": null,
        "dollar_based_amount": null,
        "total_notional": {
            "amount": "1535.10",
            "currency_code": "USD",
            "currency_id": "1072fc76-1862-41ab-82c2-485837590762"
        },
        "executed_notional": {
            "amount": "1537.57",
            "currency_code": "USD",
            "currency_id": "1072fc76-1862-41ab-82c2-485837590762"
        },
        "investment_schedule_id": null
    }

    We assume that it comes ordered by time (since that's how the web does it).
    """
    yield from get_paginated_results(get_client(), ORDERS_BASE, **kwargs)
