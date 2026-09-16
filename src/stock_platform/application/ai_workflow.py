from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from stock_platform.application.ai import (
    AIAnalysisRequest,
    AIProviderRegistry,
    execute_ai_analysis_with_registry,
)
from stock_platform.application.queries import MAXIMUM_FILTER_COUNT, QueryFilter
from stock_platform.domain.ai import (
    AI_WORKFLOW_STAGES,
    AIAnalysisIntent,
    AIWorkflowArtifact,
    AIWorkflowStageResult,
    AIWorkflowStageType,
    workflow_identifier,
)
from stock_platform.domain.common import Failure, Result, Success
from stock_platform.domain.research import DataSnapshotManifest


@dataclass(frozen=True, slots=True)
class AIWorkflowRequest:
    """The immutable input shared by every fixed lifecycle stage."""

    entity: str
    snapshot_id: str
    sort_field: str
    filters: tuple[QueryFilter, ...] = ()
    metric_field: str | None = None
    provider_id: str | None = None


@dataclass(frozen=True, slots=True)
class AIWorkflowBuildIssue:
    """A pre-analysis gate failure carrying the same local-only boundary."""

    statement: str


_STAGE_INTENTS: dict[AIWorkflowStageType, AIAnalysisIntent] = {
    "INGESTION_READINESS": "OVERVIEW",
    "DATA_QUALITY": "OVERVIEW",
    "RESEARCH_REVIEW": "RANGE",
    "RISK_DECISION": "VOLATILITY",
    "REPORT_BRIEFING": "CENTRAL_TENDENCY",
}

_STAGE_ACTIONS: dict[AIWorkflowStageType, str] = {
    "INGESTION_READINESS": "Ingestion stays pending until this dataset review is approved.",
    "DATA_QUALITY": "Quality review is bounded by the pinned rule set and cutoff.",
    "RESEARCH_REVIEW": "Research review uses only rows admitted by the pinned snapshot.",
    "RISK_DECISION": "Risk review reports observed dispersion without investment advice.",
    "REPORT_BRIEFING": "Briefing references the prior stage analyses and their evidence.",
}


def execute_ai_workflow(
    request: AIWorkflowRequest,
    catalog: Mapping[tuple[str, str], Sequence[Mapping[str, Any]]],
    snapshots: Mapping[str, DataSnapshotManifest],
    registry: AIProviderRegistry,
) -> Result[AIWorkflowArtifact, AIWorkflowBuildIssue]:
    """Run all lifecycle gates in fixed order through one registered provider."""
    if len(request.filters) > MAXIMUM_FILTER_COUNT:
        return Failure(AIWorkflowBuildIssue("AI filter limit exceeded"))
    selected_provider_id = request.provider_id or registry.default_provider_id
    try:
        registry.resolve(selected_provider_id)
    except LookupError:
        return Failure(AIWorkflowBuildIssue("AI provider is not registered"))
    if request.snapshot_id not in snapshots:
        return Failure(AIWorkflowBuildIssue("AI snapshot not pinned"))

    stage_results: list[AIWorkflowStageResult] = []
    for stage in AI_WORKFLOW_STAGES:
        analysis_request = AIAnalysisRequest(
            entity=request.entity,
            snapshot_id=request.snapshot_id,
            intent=_STAGE_INTENTS[stage],
            sort_field=request.sort_field,
            filters=request.filters,
            metric_field=request.metric_field,
            provider_id=request.provider_id,
        )
        analysis_result = execute_ai_analysis_with_registry(
            analysis_request,
            catalog,
            snapshots,
            registry,
        )
        if isinstance(analysis_result, Failure):
            return Failure(AIWorkflowBuildIssue(analysis_result.error.statement))
        analysis_artifact = analysis_result.value
        stage_results.append(
            AIWorkflowStageResult(
                stage=stage,
                analysis_id=analysis_artifact.analysis_id,
                summary=f"{_STAGE_ACTIONS[stage]} {analysis_artifact.summary}",
            )
        )
    workflow_artifact = AIWorkflowArtifact(
        workflow_id="pending",
        snapshot_id=request.snapshot_id,
        provider_id=selected_provider_id,
        intent=_STAGE_INTENTS["RESEARCH_REVIEW"],
        filters=tuple((filter_.field, filter_.value) for filter_ in request.filters),
        stages=tuple(stage_results),
    )
    return Success(replace(workflow_artifact, workflow_id=workflow_identifier(workflow_artifact)))
