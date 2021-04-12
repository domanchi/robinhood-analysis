import datetime
from typing import Any
from typing import Dict
from typing import Iterator

from ..client import get_client
from ..util import get_paginated_results
from pyrh.urls import ACH_BASE


def get_investment_as_of_date(date: datetime.date) -> float:
    # TODO: calculate ROI. for cash injections between the calculated period, we need to
    # count different ROIs (before the cash injection, and after the cash injection), then
    # somehow merge those two ratios together.
    amount = 0.0
    for transfer in _get_raw_transfer_data():
        if transfer['state'] != 'completed':
            continue

        updated_date = datetime.datetime.strptime(
            transfer['updated_at'].rstrip('Z').split('.')[0],
            '%Y-%m-%dT%H:%M:%S',
        ).date()
        if updated_date > date:
            continue

        if transfer['direction'] == 'deposit':
            amount += float(transfer['amount'])
        else:
            amount -= float(transfer['amount'])

    return amount


def _get_raw_transfer_data() -> Iterator[Dict[str, Any]]:
    """
    :returns: a list of transfers in the following format
    {
        "id": "<UUID4>",
        "ref_id": "<UUID4>",
        "url": "https://api.robinhood.com/ach/transfers/<UUID4>/",
        "cancel": null,
        "ach_relationship": "https://api.robinhood.com/ach/relationships/<UUID4>/",
        "account": "https://api.robinhood.com/accounts/<accountID>/",
        "amount": "10000.00",
        "direction": "deposit",
        "state": "completed",
        "fees": "0.00",
        "status_description": "",
        "scheduled": false,
        "expected_landing_date": "2020-03-31",
        "early_access_amount": "0.00",
        "created_at": "2020-03-25T15:30:14.225082Z",
        "updated_at": "2020-03-31T13:00:57.399635Z",
        "rhs_state": "submitted",
        "expected_sweep_at": "2020-03-26T21:00:00Z",
        "expected_landing_datetime": "2020-03-31T13:00:00Z",
        "investment_schedule_id": null
    }
    """
    yield from get_paginated_results(get_client(), ACH_BASE / 'transfers/')
