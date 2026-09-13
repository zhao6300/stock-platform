from __future__ import annotations

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.application.queries import (
    QueryFilter,
    ResearchQuery,
    execute_research_query,
)


@given(
    filters=st.lists(st.sampled_from(("identifier", "close")), max_size=20),
)
def test_queries_leave_catalog_input_unchanged(
    filters: list[tuple[str, str]],
) -> None:
    row = {"identifier": "2025-01-01", "close": Decimal("10")}
    catalog = {("snapshot-1", "daily_bar"): (row,)}
    query = ResearchQuery(
        entity="daily_bar",
        snapshot_id="snapshot-1",
        sort_field="identifier",
        filters=tuple(
            QueryFilter(field, {"identifier": "2025-01-01", "close": "10"}[field])
            for field in filters
        ),
    )
    input_row = dict(row)

    result = execute_research_query(query, catalog)

    assert row == input_row
    assert catalog[("snapshot-1", "daily_bar")] == (input_row,)
    assert result is not None
    assert result.value.rows == ((("close", "10"), ("identifier", "2025-01-01")),)
