from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from stock_platform.application.queries import (
    QueryFilter,
    ResearchQuery,
    execute_research_query,
)

type MarketInstrumentPair = tuple[str, str]


class ArrowQueryService:
    """Whitelisted purely functional query service backed by Arrow."""

    def __init__(self, rows: Mapping[tuple[str, str], Any]) -> None:
        self._rows = rows

    def open(self, market: str, instrument_type: str) -> Any:
        return self._rows[(market, instrument_type)]

    def execute(
        self,
        query: ResearchQuery,
        sort_field: str,
        filters: tuple[QueryFilter, ...],
    ) -> Any:
        return execute_research_query(
            ResearchQuery(
                entity=query.entity,
                snapshot_id=query.snapshot_id,
                sort_field=sort_field,
                filters=filters,
            ),
            self._rows,
        )
