import datetime
from collections import defaultdict
from collections import deque
from typing import Any
from typing import DefaultDict
from typing import Deque
from typing import Iterator
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Union

import pandas as pd

from ...models import Side
from ...models.option import OptionStrategy
from ...models.option import OptionTrade
from ...models.stock import StockSplit
from ...models.stock import StockTrade
from ..database.stock_split import StockSplitDBLogic
from ..trades import get_options_orders
from ..trades import get_stock_orders


class Stock(NamedTuple):
    date: datetime.date
    price: float
    quantity: float


class Trade(NamedTuple):
    date: datetime.date
    price: float


class Sale(NamedTuple):
    name: str
    bought: Trade
    sold: Trade
    quantity: float
    earnings: float


def get(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    :param from_date: YYYY-MM-DD format
    :param to_date: YYYY-MM-DD format
    """
    data: List[List[Any]] = []
    for sale in _get_trades(
        from_date=datetime.datetime.strptime(from_date, '%Y-%m-%d').date(),
        to_date=datetime.datetime.strptime(to_date, '%Y-%m-%d').date(),
    ):
        data.append([
            sale.name,
            sale.bought.date,
            round(sale.bought.price, 2),
            sale.sold.date,
            round(sale.sold.price, 2),
            # assumes we don't have partial purchases (though supported)
            int(sale.quantity),
            round(sale.earnings, 2),
        ])

    return pd.DataFrame(
        data,
        columns=[
            'Name',
            'Date Bought',
            'Price Bought',
            'Date Sold',
            'Price Sold',
            'Quantity',
            'Earnings',
        ],
    )


def _get_trades(
    from_date: Optional[datetime.date] = None,
    to_date: Optional[datetime.date] = None,
) -> Iterator[Sale]:
    portfolio = Portfolio()
    for event in _get_events(to_date):
        if isinstance(event, StockTrade):
            if event.side == Side.BUY:
                portfolio.buy(event)
            else:
                yield from filter(
                    lambda sale: sale.sold.date >= from_date,
                    portfolio.sell(event),
                )
        elif isinstance(event, StockSplit):
            portfolio.apply_split(event)
        elif isinstance(event, OptionStrategy):
            for leg in event.legs:
                if leg.side == Side.BUY:
                    portfolio.buy_option(leg)
                else:
                    yield from filter(
                        lambda sale: sale.sold.date >= from_date,
                        portfolio.sell_option(leg),
                    )


def _get_events(
    to_date: Optional[datetime.date] = None,
) -> Iterator[Union[OptionStrategy, StockSplit, StockTrade]]:
    stock_trades = {
        item.date: item
        for item in get_stock_orders(
            to_date=to_date,
            most_recent_first=False,
        )
    }
    stock_splits = {
        item.date: item
        for item in StockSplitDBLogic().get()
    }
    options_trades = {
        item.date: item
        for item in get_options_orders(to_date=to_date)
    }

    events = sorted({**options_trades, **stock_splits, **stock_trades}.items())
    for event in map(lambda x: x[1], events):
        yield event


class Portfolio:
    def __init__(self) -> None:
        self.instruments: DefaultDict[Deque[List[Stock]]] = defaultdict(
            lambda: deque([]),
        )

    def buy(self, trade: StockTrade) -> None:
        self.instruments[trade.name].append(
            Stock(
                date=trade.date.date(), price=trade.price,
                quantity=trade.quantity,
            ),
        )

    def buy_option(self, trade: OptionTrade) -> None:
        self.instruments[trade.option.serialized_name].append(
            Stock(
                date=trade.date.date(), price=trade.price,
                quantity=trade.quantity,
            ),
        )

    def sell(self, trade: StockTrade) -> Iterator[Sale]:
        quantity = trade.quantity
        while quantity:
            try:
                # Assumes FIFO
                item = self.instruments[trade.name].popleft()
            except IndexError:
                # Assumes no selling of items you don't have.
                raise IndexError(
                    f'Attempting to sell {quantity} more {trade.name} than you own.',
                )

            if item.quantity <= quantity:
                quantity_sold = item.quantity
            else:
                self.instruments[trade.name].appendleft(
                    Stock(
                        date=item.date, price=item.price,
                        quantity=item.quantity - quantity,
                    ),
                )
                quantity_sold = quantity

            quantity -= quantity_sold
            earnings = quantity_sold * (trade.price - item.price)
            yield Sale(
                name=trade.name,
                bought=Trade(date=item.date, price=item.price),
                sold=Trade(date=trade.date.date(), price=trade.price),
                quantity=quantity_sold,
                earnings=earnings,
            )

    def sell_option(self, trade: OptionTrade) -> Iterator[Sale]:
        for sale in self.sell(
            StockTrade(
                id=0,
                uuid='does-not-matter',
                name=trade.option.serialized_name,
                side=trade.side,
                date=trade.date,
                price=trade.price,
                quantity=trade.quantity,
            ),
        ):
            yield Sale(
                name=sale.name,
                bought=sale.bought,
                sold=sale.sold,
                quantity=sale.quantity,
                earnings=sale.earnings * 100,
            )

    def apply_split(self, info: StockSplit) -> None:
        if info.from_amount < info.to_amount:
            # TODO: handle non-standard numbers (2 to 3)
            self.instruments[info.name] = deque([
                Stock(
                    date=stock.date,
                    price=stock.price / info.to_amount,
                    quantity=stock.quantity * info.to_amount,
                )
                for stock in self.instruments[info.name]
            ])
        else:
            # TODO: handle stock joins
            raise NotImplementedError
