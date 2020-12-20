from abc import abstractproperty
from contextlib import contextmanager
from enum import Enum
from functools import lru_cache
from typing import Any
from typing import Generator
from typing import Type

from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.scoping import ScopedSession
from sqlalchemy.orm.session import Session
from sqlalchemy.types import TypeDecorator


class BaseMeta(DeclarativeMeta):
    """
    Adding a little magic for DRYer code.

    This encourages the use of same-named SQLAlchemy models as table names, by
    auto-setting the table name to the class name. However, if really necessary,
    it can also be overridden.

    It also injects a default `id` column, as a primary key.
    """
    def __init__(cls, *args: Any, **kwargs: Any) -> None:
        if cls.__name__ != 'Base':
            if not hasattr(cls, '__tablename__'):
                # camel case to snake case
                cls.__tablename__ = ''.join(
                    [
                        f'_{letter.lower()}' if letter.isupper() else letter
                        for letter in cls.__name__
                    ],
                ).lstrip('_')

            if not hasattr(cls, 'id'):
                cls.id = Column(Integer, nullable=False, primary_key=True)

        super().__init__(*args)


Base = declarative_base(metaclass=BaseMeta)
Base.__repr__ = lambda self: (
    '{name}({kwargs})'.format(
        name=self.__class__.__name__,
        kwargs=', '.join(
            [
                f'{name}="{getattr(self, name)}"'
                for name in dir(self)
                if (
                    not name.startswith('_')
                    and name != 'metadata'
                    and getattr(self, name) is not None
                )
            ],
        ),
    )
)


class scoped_session(ScopedSession):
    """Exists, mainly so that we can use `connect_begin` to get an explicit session object."""
    @contextmanager
    def connect(self, readonly: bool = True) -> Generator[Session, None, None]:
        self.setup()

        session = self()
        try:
            yield session

            if not readonly:
                session.commit()

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @lru_cache(maxsize=1)
    def setup(self) -> None:
        # Since we're using an on-disk sqlite3 database (as compared to a database server),
        # let's create the tables every time to make sure all tables are created for our
        # operations.
        Base.metadata.bind = self.get_bind()
        Base.metadata.create_all()


# ENGINE_URI = ':memory:'
ENGINE_URI = 'database.sqlite3'
session = scoped_session(
    sessionmaker(
        bind=create_engine(f'sqlite+pysqlite:///{ENGINE_URI}'),
    ),
)


class SerializedEnum(TypeDecorator):
    impl = Integer

    @abstractproperty
    def ENUM(self) -> Type[Enum]:
        raise NotImplementedError

    @classmethod
    def specify(cls, enum: Type[Enum]) -> Type['SerializedEnum']:
        class SpecificSerializedEnum(cls):  # type: ignore
            ENUM = enum

        return SpecificSerializedEnum

    def process_bind_param(self, value: Any, dialect: str) -> int:
        """
        :raises: ValueError
        """
        if isinstance(value, int):
            value = self.ENUM(value)

        return value.value

    def process_result_value(self, value: int, dialect: str) -> Enum:
        return self.ENUM(value)
