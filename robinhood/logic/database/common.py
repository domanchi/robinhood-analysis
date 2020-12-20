from abc import ABCMeta
from abc import abstractproperty
from typing import Any
from typing import List

from sqlalchemy.orm import Query

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
