import datetime
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import NamedTuple
from typing import Optional

from .. import database
from ..client import get_client
from ..models.option import Option
from ..models.option import OptionStrategy
from ..models.stock import StockTrade
from ..util import get_paginated_results
from .database.option import OptionDBLogic
from .database.option_trade import OptionStrategyDBLogic
from .database.stock_trade import StockTradeDBLogic
from pyrh.urls import OPTIONS_BASE
from pyrh.urls import ORDERS_BASE


def get_stock_orders(
    ticker: Optional[str] = None,
    from_date: Optional[datetime.date] = None,
    to_date: Optional[datetime.date] = None,
    most_recent_first: bool = True,
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
    last_known_trade_date = logic.get_latest_date()
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
            if last_known_trade_date and item.date < last_known_trade_date:
                break

        for event in filter(
            lambda x: x['type'] != 'expiration',
            _get_options_events(params=parameters),
        ):
            date_string = event['updated_at']
            for trade in event['equity_components']:
                trade.update({
                    'last_transaction_at': date_string,
                    'average_price': trade['price'],
                    'cumulative_quantity': trade['quantity'],
                })

                logic.create_from_raw_payload(trade)

            if (
                last_known_trade_date
                and datetime.datetime.strptime(
                    date_string.rstrip('Z').split('.')[0],
                    '%Y-%m-%dT%H:%M:%S',
                ) < last_known_trade_date
            ):
                break

    database.session.commit()

    # Then, get results.
    query = (
        logic.filter_between_dates(from_date, to_date)
        .order_by(logic.MODEL.date.desc() if most_recent_first else logic.MODEL.date.asc())
    )
    if ticker:
        query = query.filter(StockTrade.name == ticker)

    return query.all()


def _get_raw_stock_orders(**kwargs: Any) -> Iterator[Dict[str, Any]]:
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


def get_options_orders(
    ticker: Optional[str] = None,
    from_date: Optional[datetime.date] = None,
    to_date: Optional[datetime.date] = None,
) -> List[OptionStrategy]:
    if not to_date:
        to_date = datetime.date.today()

    logic = OptionStrategyDBLogic()

    # First, make sure your data is up-to-date.
    last_known_trade_date = logic.get_latest_date()
    if not last_known_trade_date or last_known_trade_date.date() < to_date:
        parameters = {}
        if last_known_trade_date:
            # Smaller pages, since we only need to get the diff.
            parameters['page_size'] = 10

        for order in _get_raw_options_orders():
            state = order['state']
            if state != 'filled':
                continue

            item = logic.create_from_raw_payload(order)
            if last_known_trade_date and item.date < last_known_trade_date:
                break

    # Then, get results.
    query = logic.filter_between_dates(from_date, to_date)
    if ticker:
        query = query.filter(OptionStrategy.name == ticker)

    return logic.hydrate(*query.all())


def _get_raw_options_orders(**kwargs: Any) -> Iterator[Dict[str, Any]]:
    """
    :returns: a list of trades in the following format
    {
        "cancel_url": null,
        "canceled_quantity": "0.00000",
        "created_at": "2020-11-30T14:54:33.730140Z",
        "direction": "credit",
        "id": "<UUID4>",
        "legs": [
            {
                "executions": [
                    {
                        "id": "<UUID4>",
                        "price": "40.00000000",
                        "quantity": "1.00000",
                        "settlement_date": "2020-12-01",
                        "timestamp": "2020-11-30T14:59:31.455000Z"
                    }
                ],
                "id": "<UUID4>",
                "option": "https://api.robinhood.com/options/instruments/2cf55d12-07b9-49c2-8958-faad46210c7d/",    # noqa: E501
                "position_effect": "close",
                "ratio_quantity": 1,
                "side": "sell"
            }
        ],
        "pending_quantity": "0.00000",
        "premium": "4000.00000000",
        "processed_premium": "4000.00000000000000000",
        "price": "40.00000000",
        "processed_quantity": "1.00000",
        "quantity": "1.00000",
        "ref_id": "<UUID4>",
        "state": "filled",
        "time_in_force": "gfd",
        "trigger": "immediate",
        "type": "limit",
        "updated_at": "2020-11-30T14:59:31.884751Z",
        "chain_id": "<UUID4>",
        "chain_symbol": "OKTA",
        "response_category": null,
        "opening_strategy": null,
        "closing_strategy": "long_call",
        "stop_price": null
    }
    """
    # NOTE: This is BIZARRE. The trailing slash is necessary, otherwise it won't be able to find
    # the URL.
    return get_paginated_results(get_client(), OPTIONS_BASE / 'orders/', **kwargs)


class OptionExpiration(NamedTuple):
    option: Option
    quantity: float


def get_options_expirations(
    to_date: Optional[datetime.date] = None,
) -> Iterator[OptionExpiration]:
    """
    :returns: (option, quantity)
    """
    if to_date:
        to_date = to_date.strftime('%Y-%m-%d')

    logic = OptionDBLogic()
    for event in filter(
        lambda x: x['type'] == 'expiration',
        _get_options_events(),
    ):
        if to_date and to_date < event['event_date']:
            continue

        yield OptionExpiration(
            option=logic.get_from_instrument_url(event['option']),
            quantity=float(event['quantity']),
        )


def _get_options_events(**kwargs) -> Iterator[Dict[str, Any]]:
    """
    :returns: events when an option has expired.
        when an option has expired in the money, it must be converted into stock inventory.
        otherwise, it must be recorded as pure loss.
    {
        "account": "https://api.robinhood.com/accounts/<accountID>/",
        "cash_component": null,
        "chain_id": "<UUID4>",
        "created_at": "2018-09-07T20:55:03.749080Z",
        "direction": "debit",
        "equity_components": [
            {
                    "id": "<UUID4>",
                    "instrument": "https://api.robinhood.com/instruments/9c53326c-d07e-4b82-82d2-b108ec5d9530/",    # noqa: E501
                    "price": "175.0000",
                    "quantity": "100.00000000",
                    "side": "buy",
                    "symbol": "SPOT"
                }
            ],
        "event_date": "2018-09-07",
        "id": "<UUID4>",
        "option": "https://api.robinhood.com/options/instruments/824783d7-ffc8-4e1b-83f9-c1234099e9e1/",
        "position": "https://api.robinhood.com/options/positions/<UUID4>/",
        "quantity": "1.0000",
        "source_ref_id": null,
        "state": "confirmed",
        "total_cash_amount": "17500.00",
        "type": "exercise",
        "underlying_price": "177.8000",
        "updated_at": "2018-09-10T08:10:05.478568Z"
    }
    """
    yield from get_paginated_results(get_client(), OPTIONS_BASE / 'events/', **kwargs)
