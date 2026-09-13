from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from stock_platform.application.dto import DTO
from stock_platform.domain.common import (
    Failure,
    JsonValue,
    Result,
    Success,
    canonical_json,
    canonical_value,
)

MAXIMUM_FILTER_COUNT = 20
MAXIMUM_ROW_COUNT = 10_000


@dataclass(frozen=True, slots=True)
class QueryFilter(DTO):
    """One typed value-binding from the whitelist-only query surface."""

    field: str
    value: str


@dataclass(frozen=True, slots=True)
class ResearchQuery(DTO):
    """A fixed result-shape request against one pinned dataset entity."""

    entity: str
    snapshot_id: str
    sort_field: str
    filters: tuple[QueryFilter, ...] = ()


@dataclass(frozen=True, slots=True)
class QueryResult(DTO):
    """A stable query result with all mandatory provenance and metadata."""

    snapshot_id: str
    entity: str
    query_parameters: str
    applied_filter_count: int
    rows: tuple[tuple[tuple[str, object], ...], ...]
    has_more: bool


@dataclass(frozen=True, slots=True)
class FilterLimitError:
    """A query was rejected before any result could change."""

    permitted_maximum: int


type ResearchQueryResult = Result[QueryResult, FilterLimitError]


def execute_research_query(
    query: ResearchQuery,
    catalog: Mapping[tuple[str, str], Sequence[Mapping[str, Any]]],
) -> ResearchQueryResult:
    """Return a stable, bounded projection from the pinned catalog."""
    if len(query.filters) > MAXIMUM_FILTER_COUNT:
        return Failure(FilterLimitError(MAXIMUM_FILTER_COUNT))
    if not query.snapshot_id or query.entity not in RESEARCH_ENTITIES:
        return Failure(FilterLimitError(MAXIMUM_FILTER_COUNT))
    rows = catalog.get((query.snapshot_id, query.entity), ())
    candidates = [
        row
        for row in rows
        if all(_filter_matches(item, row.get(item.field)) for item in query.filters)
    ]
    candidates.sort(key=_sort_key(query.sort_field))
    selected = candidates[:MAXIMUM_ROW_COUNT]
    has_more = len(candidates) > MAXIMUM_ROW_COUNT
    return Success(
        QueryResult(
            snapshot_id=query.snapshot_id,
            entity=query.entity,
            query_parameters=canonical_json(
                {
                    "entity": query.entity,
                    "filters": [item.as_dict() for item in query.filters],
                    "sort": query.sort_field,
                    "snapshot_id": query.snapshot_id,
                }
            ),
            applied_filter_count=len(query.filters),
            rows=tuple(
                tuple(
                    (field_name, canonical_value(row[field_name]))
                    for field_name in sorted(row)
                )
                for row in selected
            ),
            has_more=has_more,
        )
    )


RESEARCH_ENTITIES = frozenset(
    {
        "security_master",
        "daily_bar",
        "fund_nav",
        "trading_calendar",
        "adjustment_factor",
        "quality_status",
    }
)


def _filter_matches(filter_: QueryFilter, value: object) -> bool:
    return str(value) == filter_.value


def _sort_key(field: str) -> Callable[[Mapping[str, Any]], tuple[JsonValue, ...]]:
    def key(row: Mapping[str, Any]) -> tuple[JsonValue, ...]:
        return (canonical_value(row.get(field)),)

    return key
