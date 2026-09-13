from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.research import (
    DataSnapshotManifest,
    ResearchDateRange,
    ResearchManifest,
    missing_replay_artifacts,
)


@given(
    snapshot=st.booleans(),
    adjustment=st.booleans(),
    quality=st.booleans(),
    logic=st.booleans(),
    environment=st.booleans(),
)
def test_replay_uses_pinned_artifacts_and_collects_absences(
    snapshot: bool,
    adjustment: bool,
    quality: bool,
    logic: bool,
    environment: bool,
) -> None:
    manifest = ResearchManifest(
        run_id=UUID("00000000-0000-7000-8000-000000000000"),
        snapshot_id="snapshot-1",
        security_scope=("security-1",),
        date_range=ResearchDateRange(start=date(2025, 1, 1), end=date(2025, 1, 2)),
        providers=("provider-1",),
        calendar_versions=("calendar-1",),
        adjustment_mode="UNADJUSTED",
        quality_rule_version="quality-1",
        research_logic_version="logic-1",
        parameters=(("window", "10"),),
        dependency_environment_id="environment-1",
        generated_at=datetime(2025, 1, 2, tzinfo=UTC),
        benchmark="benchmark-1",
        cost_model="NONE",
        missing_price_policy="UNAVAILABLE",
        tradability_coverage="DAILY",
        deterministic_seed=0,
    )
    actual_snapshot = (
        DataSnapshotManifest(
            dataset_version_id="dataset-1",
            objects=(),
            security_master_versions=("master-1",),
            mapping_versions=("mapping-1",),
            calendar_versions=("calendar-1",),
            factor_series_versions=("factor-1",),
            quality_rule_set_version="quality-1",
            quality_assessment_cutoff=datetime(2025, 1, 1, tzinfo=UTC),
        )
        if snapshot
        else None
    )
    repositories = {
        "calendar": ["calendar-1"] if adjustment else [],
        "adjustment_mode": ["UNADJUSTED"] if adjustment else [],
        "quality_rule": ["quality-1"] if quality else [],
        "research_logic": ["logic-1"] if logic else [],
        "dependency_environment": ["environment-1"] if environment else [],
    }

    missing = missing_replay_artifacts(manifest, actual_snapshot, repositories)
    expected_kinds = [
        kind
        for kind, available in {
            "snapshot": snapshot,
            "calendar": adjustment,
            "adjustment_mode": adjustment,
            "quality_rule": quality,
            "research_logic": logic,
            "dependency_environment": environment,
        }.items()
        if not available
    ]
    assert tuple(item.kind for item in missing) == tuple(expected_kinds)
