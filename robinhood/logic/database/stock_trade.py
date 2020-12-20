import datetime
from typing import Any
from typing import Dict
from typing import Optional

from sqlalchemy.orm import Query
from sqlalchemy.sql.expression import func

from ... import database
from ...models import Side
from ...models.stock import StockTrade as StockTradeModel
from .common import BaseDBLogic
from .stock import StockDBLogic


class StockTradeDBLogic(BaseDBLogic):
    @property
    def MODEL(self) -> StockTradeModel:
        return StockTradeModel

    def create_from_raw_payload(self, payload: Dict[str, Any]) -> StockTradeModel:
        ticker = StockDBLogic().get_from_instrument_url(payload['instrument'])

        result = self.get(uuid=payload['id'])
        if result:
            return result[0]

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

    def get_last_known_trade_date(self) -> Optional[datetime.datetime]:
        return (
            database.session.query(self.MODEL.date, func.max(self.MODEL.date))
            .one()
            .date
        )

    def filter_trades_between_dates(
        self,
        from_date: Optional[datetime.date] = None,
        to_date: Optional[datetime.date] = None,
    ) -> Query:
        query = database.session.query(self.MODEL)

        if from_date:
            query = query.filter(self.MODEL.date >= from_date)
        if to_date:
            query = query.filter(self.MODEL.date <= to_date)

        return query
