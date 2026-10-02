import os
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


@lru_cache
def get_engine() -> Engine:
    return make_engine(os.environ["DATABASE_URL"])


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
