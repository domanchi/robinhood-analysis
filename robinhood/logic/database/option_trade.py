import datetime
from typing import Any
from typing import Dict
from typing import List

from ... import database
from ...models import Side
from ...models.option import OptionStrategy as OptionStrategyModel
from ...models.option import OptionStrategyLegs as OptionStrategyLegsModel
from ...models.option import OptionStrategyType
from ...models.option import OptionTrade as OptionTradeModel
from .common import BaseDBLogic
from .common import DateMixin
from .option import OptionDBLogic


class OptionStrategyDBLogic(DateMixin, BaseDBLogic):
    @property
    def MODEL(self) -> OptionStrategyModel:
        return OptionStrategyModel

    def create_from_raw_payload(self, payload: Dict[str, Any]) -> OptionStrategyModel:
        result = self.get(uuid=payload['id'])
        if result:
            return result[0]

        if payload['opening_strategy']:
            strategy_type = payload['opening_strategy']
            strategy_side = Side.BUY
        else:
            strategy_type = payload['closing_strategy']
            strategy_side = Side.SELL

        strategy = self.create(
            uuid=payload['id'],
            name=payload['chain_symbol'],
            side=strategy_side,
            type=OptionStrategyType(strategy_type),
            date=datetime.datetime.strptime(
                payload['updated_at'].rstrip('Z').split('.')[0],
                '%Y-%m-%dT%H:%M:%S',
            ),
        )
        strategy.legs = []

        trade_logic = OptionTradeDBLogic()
        leg_logic = OptionStrategyLegsDBLogic()
        for leg in payload['legs']:
            item = trade_logic.create_from_raw_payload(leg)
            leg_logic.create(strategy_id=strategy.id, trade_id=item.id)

            strategy.legs.append(item)

        database.session.commit()
        return strategy

    def hydrate(self, *items: OptionStrategyModel) -> List[OptionStrategyModel]:
        # TODO: We probably can improve this with a join.
        trade_logic = OptionTradeDBLogic()
        leg_logic = OptionStrategyLegsDBLogic()
        for item in items:
            item.legs = list(
                trade_logic.get_by_ids(
                    *[
                        entry.trade_id
                        for entry in leg_logic.get(strategy_id=item.id)
                    ]
                ).values(),
            )

        return items


class OptionTradeDBLogic(BaseDBLogic):
    @property
    def MODEL(self) -> OptionTradeModel:
        return OptionTradeModel

    def create_from_raw_payload(self, payload: Dict[str, Any]) -> OptionTradeModel:
        result = self.get(uuid=payload['id'])
        if result:
            return result[0]

        option = OptionDBLogic().get_from_instrument_url(payload['option'])

        date = None
        price = 0
        quantity = 0
        for execution in payload['executions']:
            if not date:
                # NOTE: It looks like Robinhood supports "Good till Cancelled" options orders,
                # so technically, you could have a leg that executes over multiple days. This
                # would result in multiple `OptionTrade` items created, which I'm not sure what
                # to do with currently.
                #
                # Therefore, I'm just going to assume this feature is disabled (I don't currently
                # use it anyway), to simplify our data model. As such, we'll just take the first
                # date of execution.
                date = execution['timestamp']

            price += float(execution['price'])
            quantity += float(execution['quantity'])

        output = self.create(
            uuid=payload['id'],
            option=option.id,
            side=Side(payload['side']),
            date=datetime.datetime.strptime(
                date.rstrip(
                    'Z',
                ).split('.')[0], '%Y-%m-%dT%H:%M:%S',
            ),
            price=price / len(payload['executions']),
            quantity=quantity / len(payload['executions']),
        )

        database.session.commit()
        return output

    def hydrate(self, *items: OptionTradeModel) -> List[OptionTradeModel]:
        options = OptionDBLogic().get_by_ids(*[item.option for item in items])
        for item in items:
            item.option = options[item.option]

        return items


class OptionStrategyLegsDBLogic(BaseDBLogic):
    @property
    def MODEL(self) -> OptionStrategyLegsModel:
        return OptionStrategyLegsModel
