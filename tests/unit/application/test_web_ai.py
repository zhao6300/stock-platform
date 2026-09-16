from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import status
from fastapi.testclient import TestClient

from stock_platform.domain.research import DataObjectReference, DataSnapshotManifest
from stock_platform.infrastructure.ai.reasoner import LocalEvidenceReasoner
from stock_platform.web.main import app, container

HEADERS = {"x-csrf-token": "csrf", "idempotency-key": "key"}


def test_http_ai_analysis_returns_a_pinned_evidence_artifact() -> None:
    expected_row_count = 2
    manifest = DataSnapshotManifest(
        dataset_version_id="http-dataset",
        objects=(DataObjectReference(sha256="0" * 64, schema_id="bars-v1", rows=2),),
        security_master_versions=(),
        mapping_versions=(),
        calendar_versions=(),
        factor_series_versions=(),
        quality_rule_set_version="rules-v1",
        quality_assessment_cutoff=datetime(2026, 1, 31, tzinfo=UTC),
    )
    snapshot_id = container.create_snapshot(manifest)
    rows: tuple[dict[str, Any], ...] = (
        {"security_id": "A", "close": 10},
        {"security_id": "B", "close": 12},
    )
    container.catalog[(snapshot_id, "daily_bar")] = rows
    with TestClient(app, client=("127.0.0.1", 51769)) as client:
        response = client.post(
            "/api/v1/research/ai-analysis",
            json={
                "entity": "daily_bar",
                "snapshot_id": snapshot_id,
                "intent": "RANGE",
                "sort_field": "close",
                "metric_field": "close",
            },
            headers=HEADERS,
        )
    body = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert body["row_count"] == expected_row_count
    assert body["evidence"][0]["snapshot_id"] == snapshot_id
    assert any("range of close" in finding["statement"] for finding in body["findings"])
    assert body["analysis_id"] in container.ai_results
    assert isinstance(container.ai_reasoner, LocalEvidenceReasoner)


def test_http_lists_ai_providers_without_provider_details() -> None:
    with TestClient(app, client=("127.0.0.1", 51769)) as client:
        response = client.get(
            "/api/v1/research/ai-providers",
            headers={"x-csrf-token": "csrf"},
        )

    body = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert body["providers"] == ["local-evidence-reasoner"]
    assert body["default_provider"] == "local-evidence-reasoner"


def test_http_ai_workflow_registers_a_five_stage_artifact() -> None:
    expected_stage_count = 5
    manifest = DataSnapshotManifest(
        dataset_version_id="http-workflow-dataset",
        objects=(DataObjectReference(sha256="0" * 64, schema_id="bars-v1", rows=2),),
        security_master_versions=(),
        mapping_versions=(),
        calendar_versions=(),
        factor_series_versions=(),
        quality_rule_set_version="rules-v1",
        quality_assessment_cutoff=datetime(2026, 1, 31, tzinfo=UTC),
    )
    snapshot_id = container.create_snapshot(manifest)
    rows: tuple[dict[str, Any], ...] = (
        {"security_id": "A", "close": 10},
        {"security_id": "B", "close": 12},
    )
    container.catalog[(snapshot_id, "daily_bar")] = rows
    with TestClient(app, client=("127.0.0.1", 51769)) as client:
        response = client.post(
            "/api/v1/research/ai-workflow",
            json={
                "entity": "daily_bar",
                "snapshot_id": snapshot_id,
                "intent": "RANGE",
                "sort_field": "close",
                "metric_field": "close",
            },
            headers=HEADERS,
        )

    body = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(body["stages"]) == expected_stage_count
    assert [stage["stage"] for stage in body["stages"]] == [
        "INGESTION_READINESS",
        "DATA_QUALITY",
        "RESEARCH_REVIEW",
        "RISK_DECISION",
        "REPORT_BRIEFING",
    ]
    assert body["workflow_id"] in container.ai_workflows
