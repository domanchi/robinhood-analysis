from collections import defaultdict
from typing import Any
from typing import Dict
from typing import List

from ..client import get_client
from ..util import get_paginated_results
from .stocks import get_stock_ticker_from_instrument
from pyrh.robinhood import Robinhood
from pyrh.urls import ORDERS_BASE


def get_orders() -> Dict[str, List[Dict[str, Any]]]:
    """
    :returns: abridged orders, grouped by stock ticker.
        {
            "side": "sell",
            "shares": 34.00000000,
            "price": 45.22260000,
            "ticker": "WB",
            "date": "2020-11-20T15:28:20.706000Z",
            "state": "filled",
        }

        This does not include crypto trades, or option trades.
    """
    client = get_client()

    orders = _get_raw_orders(client)

    output = defaultdict(list)
    for order in orders:
        state = order['state']
        if state != 'filled':
            continue

        ticker = get_stock_ticker_from_instrument(order['instrument'])
        output[ticker].append({
            'side': order['side'],
            'shares': order['cumulative_quantity'],
            'price': order['average_price'],
            'ticker': ticker,
            'date': order['last_transaction_at'],
            'state': state,
        })

        output[ticker].append(order)

    for key, value in output.items():
        output[key] = sorted(value, key=lambda x: x['date'], reverse=True)

    return dict(output)


def _get_raw_orders(client: Robinhood) -> List[Dict[str, Any]]:
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
    """
    return get_paginated_results(client, ORDERS_BASE)
