from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from typer.testing import CliRunner

from stock_platform.cli.main import app as application
from stock_platform.cli.main import context
from stock_platform.domain.ai import parse_ai_analysis_intent
from stock_platform.domain.research import DataObjectReference, DataSnapshotManifest
from stock_platform.infrastructure.ai.reasoner import LocalEvidenceReasoner


def test_parse_ai_analysis_intent_only_accepts_whitelisted_features() -> None:
    assert parse_ai_analysis_intent(" overview ") == "OVERVIEW"
    assert parse_ai_analysis_intent("central_tendency") == "CENTRAL_TENDENCY"
    assert parse_ai_analysis_intent("freform") is None


def test_cli_ai_analyze_runs_the_registered_local_reasoner() -> None:
    context.container.ai_reasoner = LocalEvidenceReasoner()
    manifest = DataSnapshotManifest(
        dataset_version_id="cli-dataset",
        objects=(DataObjectReference(sha256="0" * 64, schema_id="bars-v1", rows=2),),
        security_master_versions=(),
        mapping_versions=(),
        calendar_versions=(),
        factor_series_versions=(),
        quality_rule_set_version="rules-v1",
        quality_assessment_cutoff=datetime(2026, 1, 31, tzinfo=UTC),
    )
    snapshot_id = context.container.create_snapshot(manifest)
    rows: tuple[dict[str, Any], ...] = (
        {"security_id": "A", "close": 10},
        {"security_id": "B", "close": 12},
    )
    context.container.catalog[(snapshot_id, "daily_bar")] = rows

    result = CliRunner().invoke(
        application,
        [
            "ai-analyze",
            "daily_bar",
            snapshot_id,
            "close",
            "--intent",
            "RANGE",
        ],
    )
    unpinned = CliRunner().invoke(
        application,
        [
            "ai-analyze",
            "daily_bar",
            "sha256:not-pinned",
            "close",
            "--intent",
            "RANGE",
        ],
    )

    assert result.exit_code == 0
    assert "analysis=ai-sha256:" in result.output
    assert "model=platform-evidence-reasoner" in result.output
    assert unpinned.exit_code != 0
    assert "error=AI snapshot not pinned" in unpinned.output


def test_cli_ai_workflow_reaches_the_registered_local_reasoner() -> None:
    manifest = DataSnapshotManifest(
        dataset_version_id="cli-workflow-dataset",
        objects=(DataObjectReference(sha256="0" * 64, schema_id="bars-v1", rows=2),),
        security_master_versions=(),
        mapping_versions=(),
        calendar_versions=(),
        factor_series_versions=(),
        quality_rule_set_version="rules-v1",
        quality_assessment_cutoff=datetime(2026, 1, 31, tzinfo=UTC),
    )
    snapshot_id = context.container.create_snapshot(manifest)
    rows: tuple[dict[str, Any], ...] = (
        {"security_id": "A", "close": 10},
        {"security_id": "B", "close": 12},
    )
    context.container.catalog[(snapshot_id, "daily_bar")] = rows

    result = CliRunner().invoke(
        application,
        [
            "ai-workflow",
            "daily_bar",
            snapshot_id,
            "close",
            "--provider",
            "local-evidence-reasoner",
        ],
    )

    assert result.exit_code == 0
    assert "workflow=ai-workflow-sha256:" in result.output
    assert "provider=local-evidence-reasoner stages=5" in result.output
    assert context.container.installed_ai_provider_ids() == ("local-evidence-reasoner",)
