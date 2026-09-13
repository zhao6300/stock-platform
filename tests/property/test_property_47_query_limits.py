from __future__ import annotations

from hypothesis import given
from hypothesis.strategies import integers

from stock_platform.application.queries import (
    MAXIMUM_FILTER_COUNT,
    MAXIMUM_ROW_COUNT,
    QueryFilter,
    ResearchQuery,
    execute_research_query,
)
from stock_platform.domain.common import Failure


@given(
    filter_count=integers(min_value=0, max_value=25),
    row_count=integers(min_value=0, max_value=10005),
)
def test_query_limits_and_metadata_are_exact(filter_count: int, row_count: int) -> None:
    rows = [{"identifier": f"{index}", "text": "a"} for index in range(row_count)]
    filters = [QueryFilter("text", "a") for _ in range(filter_count)]
    query = ResearchQuery(
        entity="daily_bar",
        snapshot_id="snapshot-1",
        sort_field="identifier",
        filters=tuple(filters),
    )

    result = execute_research_query(query, {("snapshot-1", "daily_bar"): rows})

    if filter_count > MAXIMUM_FILTER_COUNT:
        assert result.error.permitted_maximum == MAXIMUM_FILTER_COUNT
        return
    assert result.value.applied_filter_count == filter_count
    assert result.value.returned_count == min(row_count, MAXIMUM_ROW_COUNT)
    assert len(result.value.rows) == min(row_count, MAXIMUM_ROW_COUNT)
    assert result.value.has_more == (row_count > MAXIMUM_ROW_COUNT)


def test_query_rejects_unlisted_entity_and_blank_snapshot_before_catalog_access() -> None:
    result = execute_research_query(
        ResearchQuery(entity="/etc/passwd", snapshot_id="", sort_field="x"),
        catalog={("", "/etc/passwd"): ({"secret": "1"},)},
    )

    assert isinstance(result, Failure)
    assert result.error.permitted_maximum == MAXIMUM_FILTER_COUNT
