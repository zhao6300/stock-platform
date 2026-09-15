from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from stock_platform.application.ai import AIAnalysisRequest, execute_ai_analysis
from stock_platform.application.container import ApplicationContainer
from stock_platform.application.queries import QueryFilter
from stock_platform.domain.common import Failure, Success
from stock_platform.domain.research import DataObjectReference, DataSnapshotManifest
from stock_platform.infrastructure.ai.reasoner import LocalEvidenceReasoner

ROWS: tuple[dict[str, Any], ...] = (
    {"security_id": "A", "close": Decimal("10.00")},
    {"security_id": "B", "close": Decimal("12.00")},
    {"security_id": "C", "close": Decimal("14.00")},
)
ROW_COUNT = len(ROWS)


def snapshot_manifest() -> tuple[str, dict[str, DataSnapshotManifest]]:
    manifest = DataSnapshotManifest(
        dataset_version_id="test-dataset",
        objects=(DataObjectReference(sha256="0" * 64, schema_id="bars-v1", rows=len(ROWS)),),
        security_master_versions=(),
        mapping_versions=(),
        calendar_versions=(),
        factor_series_versions=(),
        quality_rule_set_version="rules-v1",
        quality_assessment_cutoff=datetime(2026, 1, 31, tzinfo=UTC),
    )
    container = ApplicationContainer()
    snapshot_id = container.create_snapshot(manifest)
    return snapshot_id, container.snapshots


def request(snapshot_id: str) -> AIAnalysisRequest:
    return AIAnalysisRequest(
        entity="daily_bar",
        snapshot_id=snapshot_id,
        intent="RANGE",
        sort_field="close",
        metric_field="close",
    )


def catalog(snapshot_id: str) -> dict[tuple[str, str], tuple[dict[str, Any], ...]]:
    return {(snapshot_id, "daily_bar"): ROWS}


def test_ai_reasoner_binds_findings_to_pinned_query() -> None:
    snapshot_id, snapshots = snapshot_manifest()

    result = execute_ai_analysis(
        request(snapshot_id),
        catalog(snapshot_id),
        snapshots,
        LocalEvidenceReasoner(),
    )

    assert isinstance(result, Success)
    artifact = result.value
    assert artifact.evidence[0].entity == "daily_bar"
    assert artifact.evidence[0].row_count == ROW_COUNT
    assert artifact.evidence[0].result_sha256.startswith("sha256") is False
    assert artifact.evidence[0].result_sha256 != ""
    assert any("range of close" in finding.statement for finding in artifact.findings)
    assert all(finding.evidence_ids == ("evidence-001",) for finding in artifact.findings)


def test_ai_output_is_deterministic_for_the_same_query() -> None:
    snapshot_id, snapshots = snapshot_manifest()
    provider = LocalEvidenceReasoner()

    first = execute_ai_analysis(request(snapshot_id), catalog(snapshot_id), snapshots, provider)
    second = execute_ai_analysis(request(snapshot_id), catalog(snapshot_id), snapshots, provider)

    assert isinstance(first, Success)
    assert isinstance(second, Success)
    assert first.value.analysis_id == second.value.analysis_id
    assert first.value.as_dict() == second.value.as_dict()


def test_ai_rejects_unpinned_snapshots_before_running_a_query() -> None:
    result = execute_ai_analysis(
        request("sha256:not-pinned"),
        catalog("sha256:not-pinned"),
        {},
        LocalEvidenceReasoner(),
    )

    assert isinstance(result, Failure)
    assert result.error.statement == "AI snapshot not pinned"


def test_ai_applies_exact_filters_before_explaining_results() -> None:
    snapshot_id, snapshots = snapshot_manifest()
    filtered = AIAnalysisRequest(
        entity="daily_bar",
        snapshot_id=snapshot_id,
        intent="CENTRAL_TENDENCY",
        sort_field="close",
        filters=(QueryFilter("security_id", "B"),),
        metric_field="close",
    )

    result = execute_ai_analysis(
        filtered,
        catalog(snapshot_id),
        snapshots,
        LocalEvidenceReasoner(),
    )

    assert isinstance(result, Success)
    assert result.value.evidence[0].row_count == 1
    assert result.value.evidence[0].filters == (("security_id", "B"),)
    assert any("mean of close is 12" in finding.statement for finding in result.value.findings)
