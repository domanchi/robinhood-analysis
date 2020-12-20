import datetime
from abc import ABCMeta
from abc import abstractproperty
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from sqlalchemy.orm import Query
from sqlalchemy.sql.expression import func

from ... import database
from ...database import Base


class BaseDBLogic(metaclass=ABCMeta):
    @abstractproperty
    def MODEL(self) -> Base:
        raise NotImplementedError

    def create(self, **kwargs: Any) -> Base:
        item = self.MODEL(**kwargs)
        database.session.add(item)

        return item

    def get(self, **filters: Any) -> List[Base]:
        return self.get_filtered_query(**filters).all()

    def get_filtered_query(self, **filters: Any) -> Query:
        query = database.session.query(self.MODEL)
        for key, value in filters.items():
            query = query.filter(getattr(self.MODEL, key) == value)

        return query

    def get_by_ids(self, *ids: int) -> Dict[int, Base]:
        return {
            item.id: item
            for item in database.session.query(self.MODEL).filter(
                self.MODEL.id.in_(ids),
            )
        }


class DateMixin:
    def filter_between_dates(
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

    def get_latest_date(self) -> Optional[datetime.datetime]:
        return (
            database.session.query(self.MODEL.date, func.max(self.MODEL.date))
            .one()
            .date
        )
