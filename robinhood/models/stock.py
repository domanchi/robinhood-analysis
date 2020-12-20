from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import String

from . import Side
from ..database import Base
from ..database import SerializedEnum


class Stock(Base):
    uuid = Column(String, nullable=False, unique=True)

    # NOTE: Interestingly, there are multiple UUIDs mapping to the same stock ticker.
    # This is because the ticker is a mere abstraction for the underlying stock information
    # For example, if the stock's official name changes, but the ticker stays the same, the UUID
    # will be different.
    name = Column(
        String,
        nullable=False,
    )


class StockTrade(Base):
    uuid = Column(String, nullable=False, unique=True)

    name = Column(String, nullable=False)
    side = Column(
        SerializedEnum.specify(Side),
        nullable=False,
    )
    date = Column(DateTime, nullable=False)

    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
