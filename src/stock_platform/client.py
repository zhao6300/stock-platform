from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from stock_platform.application.ai import (
    AIAnalysisRequest,
    AIArtifactBuildIssue,
    AIResearchProvider,
    execute_ai_analysis,
)
from stock_platform.application.queries import (
    ResearchQuery,
    ResearchQueryResult,
    execute_research_query,
)
from stock_platform.domain.ai import AIAnalysisArtifact
from stock_platform.domain.common import Result
from stock_platform.domain.research import DataSnapshotManifest
from stock_platform.infrastructure.ai.reasoner import LocalEvidenceReasoner


@dataclass(frozen=True, slots=True)
class SnapshotResearchClient:
    """A read-only facade around one pinned snapshot."""

    snapshot_id: str
    catalog: Mapping[tuple[str, str], Sequence[Mapping[str, Any]]]
    reasoner: AIResearchProvider = field(default_factory=LocalEvidenceReasoner)

    def query(self, query: ResearchQuery) -> ResearchQueryResult:
        """Run through the application layer with the pinned catalog."""
        if query.snapshot_id != self.snapshot_id:
            return execute_research_query(query, {})
        return execute_research_query(query, self.catalog)

    def analyze(
        self,
        request: AIAnalysisRequest,
        snapshot_manifest: DataSnapshotManifest | None = None,
    ) -> Result[AIAnalysisArtifact, AIArtifactBuildIssue]:
        """Run the local evidence reasoner against this pinned snapshot."""
        return execute_ai_analysis(
            request,
            self.catalog,
            {} if snapshot_manifest is None else {self.snapshot_id: snapshot_manifest},
            self.reasoner,
        )


def open_snapshot(
    snapshot_id: str,
    catalog: Mapping[tuple[str, str], Sequence[Mapping[str, Any]]],
) -> SnapshotResearchClient:
    """Create a read-only snapshot view."""
    return SnapshotResearchClient(snapshot_id, MappingProxyType(catalog))
