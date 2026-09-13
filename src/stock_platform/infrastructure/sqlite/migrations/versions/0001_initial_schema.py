"""Initial schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-01-01 00:00:00
"""

from __future__ import annotations

from alembic import op

from stock_platform.infrastructure.sqlite.models import (
    APPEND_ONLY_TABLES,
    Base,
    guard_sql,
)

revision: str = "0001_initial_schema"
down_revision: str | None = None


def upgrade() -> None:
    connection = op.get_bind()
    Base.metadata.create_all(connection, checkfirst=True)
    for table_name in sorted(APPEND_ONLY_TABLES):
        op.execute(guard_sql(table_name, "UPDATE"))
        op.execute(guard_sql(table_name, "DELETE"))


def downgrade() -> None:
    Base.metadata.drop_all(op.get_bind())
