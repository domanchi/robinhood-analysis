from typing import Any
from typing import List

from ...database import Base
from ...models.stock import StockSplit as StockSplitModel
from .common import BaseDBLogic
from .common import DateMixin


class StockSplitDBLogic(DateMixin, BaseDBLogic):
    @property
    def MODEL(self) -> StockSplitModel:
        return StockSplitModel

    def get(self, **filters: Any) -> List[Base]:
        return (
            self.get_filtered_query(**filters)
            .order_by(self.MODEL.date.asc())
            .all()
        )
