import datetime
from typing import Any
from typing import Dict

from ...models import Side
from ...models.stock import StockTrade as StockTradeModel
from .common import BaseDBLogic
from .common import DateMixin
from .stock import StockDBLogic


class StockTradeDBLogic(DateMixin, BaseDBLogic):
    @property
    def MODEL(self) -> StockTradeModel:
        return StockTradeModel

    def create_from_raw_payload(self, payload: Dict[str, Any]) -> StockTradeModel:
        result = self.get(uuid=payload['id'])
        if result:
            return result[0]

        ticker = StockDBLogic().get_from_instrument_url(payload['instrument'])
        return self.create(
            uuid=payload['id'],
            name=ticker.name,
            side=Side(payload['side']),
            date=datetime.datetime.strptime(
                # Clear off the %f part, because it seems that the data may sometimes
                # not include it. (!!)
                payload['last_transaction_at'].rstrip('Z').split('.')[0],
                '%Y-%m-%dT%H:%M:%S',
            ),
            price=payload['average_price'],
            quantity=payload['cumulative_quantity'],
        )
