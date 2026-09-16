from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from stock_platform.application.ai import AIProviderRegistry
from stock_platform.application.ai_workflow import AIWorkflowRequest, execute_ai_workflow
from stock_platform.application.container import ApplicationContainer
from stock_platform.domain.common import Failure, Success
from stock_platform.domain.research import DataObjectReference, DataSnapshotManifest
from stock_platform.infrastructure.ai.reasoner import LocalEvidenceReasoner

ROWS: tuple[dict[str, Any], ...] = (
    {"security_id": "A", "close": 10},
    {"security_id": "B", "close": 14},
    {"security_id": "C", "close": 16},
)


def manifest() -> DataSnapshotManifest:
    return DataSnapshotManifest(
        dataset_version_id="workflow-dataset",
        objects=(DataObjectReference(sha256="0" * 64, schema_id="bars-v1", rows=5),),
        security_master_versions=(),
        mapping_versions=(),
        calendar_versions=(),
        factor_series_versions=(),
        quality_rule_set_version="quality-rules-v1",
        quality_assessment_cutoff=datetime(2026, 1, 31, tzinfo=UTC),
    )


def snapshot_id() -> str:
    container = ApplicationContainer(ai_reasoner=LocalEvidenceReasoner())
    return container.create_snapshot(manifest())


def _snapshots(snapshot: str) -> dict[str, DataSnapshotManifest]:
    return {snapshot: manifest()}


def workflow_request(snapshot: str) -> AIWorkflowRequest:
    return AIWorkflowRequest(
        entity="daily_bar",
        snapshot_id=snapshot,
        sort_field="close",
        metric_field="close",
    )


def test_workflow_runs_fixed_lifecycle_gates_in_order() -> None:
    snapshot = snapshot_id()
    catalog = {(snapshot, "daily_bar"): ROWS}
    frozen = _snapshots(snapshot)
    registry = AIProviderRegistry(providers=(), default_provider_id="local")
    registry = registry.with_provider("local", LocalEvidenceReasoner())

    result = execute_ai_workflow(
        workflow_request(snapshot),
        catalog,
        frozen,
        registry,
    )

    assert isinstance(result, Success)
    stages = tuple(stage.stage for stage in result.value.stages)
    assert stages == (
        "INGESTION_READINESS",
        "DATA_QUALITY",
        "RESEARCH_REVIEW",
        "RISK_DECISION",
        "REPORT_BRIEFING",
    )
    assert result.value.workflow_id.startswith("ai-workflow-sha256:")
    assert all(stage.summary for stage in result.value.stages)


def test_workflow_rejects_an_unregistered_provider_before_queries() -> None:
    snapshot = snapshot_id()
    registry = AIProviderRegistry(providers=(), default_provider_id="missing")

    result = execute_ai_workflow(
        workflow_request(snapshot),
        {(snapshot, "daily_bar"): ROWS},
        _snapshots(snapshot),
        registry,
    )

    assert isinstance(result, Failure)
    assert result.error.statement == "AI provider is not registered"


def test_workflow_rejects_an_unpinned_snapshot_before_any_model_call() -> None:
    registry = AIProviderRegistry(providers=(), default_provider_id="local")
    registry = registry.with_provider("local", LocalEvidenceReasoner())

    result = execute_ai_workflow(
        workflow_request("sha256:missing"),
        {},
        {},
        registry,
    )

    assert isinstance(result, Failure)
    assert result.error.statement == "AI snapshot not pinned"
