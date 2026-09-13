from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from stock_platform.infrastructure.sqlite.models import create_sql_schema


class SQLiteUnitOfWork:
    """Explicit transaction boundary for SQLite-backed repositories."""

    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url)
        create_sql_schema(self._engine)

    @property
    def engine(self) -> Engine:
        return self._engine

    @contextmanager
    def begin(self, schema_factory: Callable[[], None] | None = None) -> Iterator[Session]:
        """Yield one session, commit on success and roll back any failure."""
        session = Session(self._engine)
        try:
            if schema_factory is not None:
                schema_factory()
            yield session
            session.commit()
        except BaseException:
            session.rollback()
            raise
        finally:
            session.close()
