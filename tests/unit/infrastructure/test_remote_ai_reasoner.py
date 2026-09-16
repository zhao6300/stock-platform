from __future__ import annotations

from datetime import UTC, datetime

from stock_platform.application.ai import (
    AIAnalysisRequest,
    AIProviderRegistry,
    execute_ai_analysis_with_registry,
)
from stock_platform.application.container import ApplicationContainer
from stock_platform.domain.common import Failure, Success
from stock_platform.domain.research import DataObjectReference, DataSnapshotManifest
from stock_platform.infrastructure.ai.reasoner import (
    AIRemoteModelRequest,
    AIRemoteModelResponse,
    LocalEvidenceReasoner,
    RemoteEvidenceReasoner,
)

ROWS: tuple[dict[str, object], ...] = (
    {"security_id": "A", "close": 10},
    {"security_id": "B", "close": 12},
)


class FakeModelClient:
    def complete(self, request: AIRemoteModelRequest) -> AIRemoteModelResponse:
        self.last_request = request
        return AIRemoteModelResponse(summary="The selected bars show a bounded range.")


class InvalidClient:
    def complete(self, request: AIRemoteModelRequest) -> AIRemoteModelResponse:
        return AIRemoteModelResponse(summary=" " * 2000)


def container() -> ApplicationContainer:
    manifest = DataSnapshotManifest(
        dataset_version_id="remote-dataset",
        objects=(DataObjectReference(sha256="0" * 64, schema_id="bars-v1", rows=2),),
        security_master_versions=(),
        mapping_versions=(),
        calendar_versions=(),
        factor_series_versions=(),
        quality_rule_set_version="rules-v1",
        quality_assessment_cutoff=datetime(2026, 1, 31, tzinfo=UTC),
    )
    result = ApplicationContainer(ai_reasoner=LocalEvidenceReasoner())
    snapshot_id = result.create_snapshot(manifest)
    result.catalog[(snapshot_id, "daily_bar")] = ROWS
    return result


def analysis_request(snapshot: str) -> AIAnalysisRequest:
    return AIAnalysisRequest(
        entity="daily_bar",
        snapshot_id=snapshot,
        intent="RANGE",
        sort_field="close",
        metric_field="close",
        provider_id="remote-briefing",
    )


def test_remote_reasoner_keeps_metrics_local_and_uses_only_the_briefing() -> None:
    holder = container()
    snapshot = next(iter(holder.snapshots))
    client = FakeModelClient()
    registry = AIProviderRegistry(providers=(), default_provider_id="remote-briefing")
    provider = RemoteEvidenceReasoner(
        provider_id="remote-briefing",
        backing_model_id="model-gateway-v1",
        client=client,
    )
    registry = registry.with_provider("remote-briefing", provider)

    result = execute_ai_analysis_with_registry(
        analysis_request(snapshot),
        holder.catalog,
        holder.snapshots,
        registry,
    )

    assert isinstance(result, Success)
    artifact = result.value
    request = client.last_request
    assert artifact.provider_id == "remote-briefing"
    assert artifact.model_id == "model-gateway-v1"
    assert artifact.summary == "The selected bars show a bounded range."
    assert artifact.metrics[0].kind == "COUNT"
    assert artifact.metrics[1].kind == "MIN"
    assert "The range of close is 2." not in artifact.summary
    assert any(item.content == "user" for item in request.messages) is False
    assert any(item.role == "system" for item in request.messages)
    assert "security_id" not in request.messages[1].content


def test_remote_reasoner_rejects_an_oversized_provider_summary() -> None:
    holder = container()
    snapshot = next(iter(holder.snapshots))
    registry = AIProviderRegistry(providers=(), default_provider_id="remote-briefing")
    registry = registry.with_provider(
        "remote-briefing",
        RemoteEvidenceReasoner(
            provider_id="remote-briefing",
            backing_model_id="invalid-model",
            client=InvalidClient(),
        ),
    )

    result = execute_ai_analysis_with_registry(
        analysis_request(snapshot),
        holder.catalog,
        holder.snapshots,
        registry,
    )

    assert isinstance(result, Failure)
    assert result.error.statement == "AI provider contract violated"
