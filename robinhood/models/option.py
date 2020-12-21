from enum import Enum

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String

from . import Side
from ..database import Base
from ..database import SerializedEnum


class OptionType(Enum):
    CALL = 'call'
    PUT = 'put'


class OptionStrategyType(Enum):
    # NOTE: We currently only assume single-leg options strategies only.
    LONG_CALL = 'long_call'
    LONG_PUT = 'long_put'
    SHORT_PUT = 'short_put'
    SHORT_CALL = 'short_call'


class Option(Base):
    """Represents a single Option contract."""
    uuid = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    type = Column(SerializedEnum.specify(OptionType), nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    strike_price = Column(Float, nullable=False)

    @property
    def serialized_name(self):
        # https://en.wikipedia.org/wiki/Option_naming_convention
        return '{ticker}{expiration_date}{type}{price}'.format(
            ticker=self.name,
            expiration_date=self.expiration_date.strftime('%y%m%d'),
            type='C' if self.type == OptionType.CALL else 'P',
            price='{:09.3f}'.format(self.strike_price).replace('.', ''),
        )


class OptionTrade(Base):
    """Represents one leg in an Options trade."""
    uuid = Column(String, nullable=False, unique=True)

    option_id = Column(Integer, ForeignKey('option.id'))
    side = Column(SerializedEnum.specify(Side), nullable=False)
    date = Column(DateTime, nullable=False)

    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)


class OptionStrategy(Base):
    uuid = Column(String, nullable=False, unique=True)

    name = Column(String, nullable=False)
    side = Column(
        SerializedEnum.specify(Side),
        nullable=False,
        doc=(
            'BUY == open strategy; SELL == close strategy. '
            'This differs from individual legs\' sides, since when you open a strategy, you may '
            'buy and sell different legs. When combined with `type`, it informs you which way '
            'the money is going.'
        ),
    )
    type = Column(SerializedEnum.specify(OptionStrategyType), nullable=False)
    date = Column(DateTime, nullable=False)


class OptionStrategyLegs(Base):
    strategy_id = Column(
        Integer, ForeignKey(
            'option_strategy.id',
        ), nullable=False,
    )
    trade_id = Column(Integer, ForeignKey('option_trade.id'), nullable=False)
