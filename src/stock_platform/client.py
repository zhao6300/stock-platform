from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from stock_platform.application.queries import (
    ResearchQuery,
    ResearchQueryResult,
    execute_research_query,
)


@dataclass(frozen=True, slots=True)
class SnapshotResearchClient:
    """A read-only facade around one pinned snapshot."""

    snapshot_id: str
    catalog: Mapping[tuple[str, str], Sequence[Mapping[str, Any]]]

    def query(self, query: ResearchQuery) -> ResearchQueryResult:
        """Run through the application layer with the pinned catalog."""
        if query.snapshot_id != self.snapshot_id:
            return execute_research_query(query, {})
        return execute_research_query(query, self.catalog)


def open_snapshot(
    snapshot_id: str,
    catalog: Mapping[tuple[str, str], Sequence[Mapping[str, Any]]],
) -> SnapshotResearchClient:
    """Create a read-only snapshot view."""
    return SnapshotResearchClient(snapshot_id, MappingProxyType(catalog))
