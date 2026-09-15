from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol, runtime_checkable

from stock_platform.application.dto import DTO
from stock_platform.application.queries import (
    RESEARCH_ENTITIES,
    QueryFilter,
    QueryResult,
    ResearchQuery,
    execute_research_query,
)
from stock_platform.domain.ai import AIAnalysisArtifact, AIAnalysisIntent
from stock_platform.domain.common import Failure, Result, Success
from stock_platform.domain.research import DataSnapshotManifest

MAXIMUM_FILTER_COUNT = 20
MAXIMUM_ROW_COUNT = 10_000

type AIAnalysisErrorType = Literal[
    "AI_FILTER_LIMIT_EXCEEDED",
    "AI_ENTITY_NOT_PERMITTED",
    "AI_INTENT_NOT_APPLICABLE",
    "AI_SNAPSHOT_NOT_PINNED",
]


AI_RESEARCH_PROVIDER_ID = "local-evidence-reasoner"


@dataclass(frozen=True, slots=True)
class AIAnalysisRequest(DTO):
    """A feature-scoped AI question tied to one immutable snapshot."""

    entity: str
    snapshot_id: str
    intent: AIAnalysisIntent
    sort_field: str
    filters: tuple[QueryFilter, ...] = ()
    metric_field: str | None = None


@dataclass(frozen=True, slots=True)
class AIArtifactBuildIssue:
    """A typed query contract failure surfaced by an AI reasoner."""

    statement: str


def execute_ai_analysis(
    request: AIAnalysisRequest,
    catalog: Mapping[tuple[str, str], Sequence[Mapping[str, Any]]],
    snapshots: Mapping[str, DataSnapshotManifest],
    provider: AIResearchProvider,
) -> Result[AIAnalysisArtifact, AIArtifactBuildIssue]:
    """Validate a pinned request, run its bounded query, then build an artifact."""
    if len(request.filters) > MAXIMUM_FILTER_COUNT:
        return Failure(AIArtifactBuildIssue("AI filter limit exceeded"))
    if request.entity not in RESEARCH_ENTITIES:
        return Failure(AIArtifactBuildIssue("AI entity not permitted"))
    snapshot = snapshots.get(request.snapshot_id)
    if snapshot is None:
        return Failure(AIArtifactBuildIssue("AI snapshot not pinned"))
    query_result = ResearchQuery(
        entity=request.entity,
        snapshot_id=request.snapshot_id,
        sort_field=request.sort_field,
        filters=request.filters,
    )
    result = execute_research_query(query_result, catalog)
    if isinstance(result, Failure):
        return Failure(AIArtifactBuildIssue("AI query limits exceeded"))
    artifact = provider.analyze(request, snapshot, result.value)
    return Success(artifact)


@runtime_checkable
class AIResearchProvider(Protocol):
    """The application port for a provenance-safe research reasoner."""

    model_id: str
    model_version: str
    prompt_template_version: str
    reasoning_rule_set_version: str

    def analyze(
        self,
        request: AIAnalysisRequest,
        snapshot: DataSnapshotManifest,
        query_result: QueryResult,
    ) -> AIAnalysisArtifact: ...
