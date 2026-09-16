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
    "AI_PROVIDER_NOT_REGISTERED",
]


AI_RESEARCH_PROVIDER_ID = "local-evidence-reasoner"


@dataclass(frozen=True, slots=True)
class AIProviderBinding:
    """One named adapter exposed through the stable research provider port."""

    provider_id: str
    provider: AIResearchProvider


@dataclass(frozen=True, slots=True)
class AIProviderRegistry:
    """A small deterministic routing boundary for many AI model providers."""

    providers: tuple[AIProviderBinding, ...]
    default_provider_id: str

    def provider_ids(self) -> tuple[str, ...]:
        """Return stable identifiers for all registered AI providers."""
        return tuple(item.provider_id for item in self.providers)

    def resolve(self, provider_id: str | None = None) -> AIResearchProvider:
        """Resolve an explicit or default provider without guessing behavior."""
        selected = provider_id or self.default_provider_id
        for binding in self.providers:
            if binding.provider_id == selected:
                return binding.provider
        raise LookupError(f"AI provider is not registered: {selected}")

    def with_provider(
        self, provider_id: str, provider: AIResearchProvider
    ) -> AIProviderRegistry:
        """Return a registry with one provider replacing an existing binding."""
        binding = AIProviderBinding(provider_id=provider_id, provider=provider)
        provider_ids = set(self.provider_ids())
        replace_default = provider_id not in provider_ids or not self.providers
        return AIProviderRegistry(
            providers=(
                *(item for item in self.providers if item.provider_id != provider_id),
                binding,
            ),
            default_provider_id=provider_id if replace_default else self.default_provider_id,
        )


@dataclass(frozen=True, slots=True)
class AIAnalysisRequest(DTO):
    """A feature-scoped AI question tied to one immutable snapshot."""

    entity: str
    snapshot_id: str
    intent: AIAnalysisIntent
    sort_field: str
    filters: tuple[QueryFilter, ...] = ()
    metric_field: str | None = None
    provider_id: str | None = None


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
    try:
        artifact = provider.analyze(request, snapshot, result.value)
    except (TypeError, ValueError):
        return Failure(AIArtifactBuildIssue("AI provider contract violated"))
    return Success(artifact)


def execute_ai_analysis_with_registry(
    request: AIAnalysisRequest,
    catalog: Mapping[tuple[str, str], Sequence[Mapping[str, Any]]],
    snapshots: Mapping[str, DataSnapshotManifest],
    registry: AIProviderRegistry,
) -> Result[AIAnalysisArtifact, AIArtifactBuildIssue]:
    """Resolve the selected provider, then run the same bounded analysis path."""
    try:
        provider = registry.resolve(request.provider_id)
    except LookupError:
        return Failure(AIArtifactBuildIssue("AI provider is not registered"))
    return execute_ai_analysis(request, catalog, snapshots, provider)


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
