from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from stock_platform.domain.research import (
    DataSnapshotManifest,
    ResearchDateRange,
    ResearchManifest,
    canonical_business_id,
    missing_replay_artifacts,
    project_snapshot,
)


def _manifest() -> ResearchManifest:
    return ResearchManifest(
        run_id=UUID("00000000-0000-7000-8000-000000000000"),
        snapshot_id="sha256:snapshot",
        security_scope=("security-1",),
        date_range=ResearchDateRange(date(2025, 1, 1), date(2025, 1, 2)),
        providers=("provider-1",),
        calendar_versions=("calendar-1",),
        adjustment_mode="UNADJUSTED",
        quality_rule_version="quality-1",
        research_logic_version="logic-1",
        parameters=(("windows", "2"),),
        dependency_environment_id="environment-1",
        generated_at=datetime(2025, 1, 2, tzinfo=UTC),
        benchmark="benchmark-1",
        cost_model="NONE",
        missing_price_policy="UNAVAILABLE",
        tradability_coverage="DAILY",
        deterministic_seed=0,
    )


def _snapshot() -> DataSnapshotManifest:
    return DataSnapshotManifest(
        dataset_version_id="dataset-1",
        objects=(),
        security_master_versions=("master-1",),
        mapping_versions=("mapping-1",),
        calendar_versions=("calendar-1",),
        factor_series_versions=("factor-1",),
        quality_rule_set_version="quality-1",
        quality_assessment_cutoff=datetime(2025, 1, 1, tzinfo=UTC),
    )


def test_missing_replay_artifacts_are_complete() -> None:
    manifest = _manifest()
    missing = missing_replay_artifacts(
        manifest,
        _snapshot(),
        {
            "calendar": {"calendar-1"},
            "adjustment_mode": {"UNADJUSTED"},
            "quality_rule": {"quality-1"},
            "research_logic": {"logic-1"},
            "dependency_environment": {"environment-1"},
        },
    )

    assert missing == ()


def test_project_snapshot_only_uses_manifest_projection() -> None:
    snapshot = _snapshot()

    projection = project_snapshot(snapshot)

    assert projection.manifest is snapshot


def test_canonical_business_id_uses_utc() -> None:
    value = canonical_business_id(datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC))

    assert value == "20260101T12:00:00Z"
