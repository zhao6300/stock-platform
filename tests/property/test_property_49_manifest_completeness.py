from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.common import canonical_json
from stock_platform.domain.research import (
    DataObjectReference,
    DataSnapshotManifest,
    ResearchDateRange,
    ResearchManifest,
    data_snapshot_id,
)


@given(
    dataset_version_id=st.text(min_size=1, max_size=8),
    object_count=st.integers(min_value=0, max_value=3),
)
def test_snapshot_ids_are_content_bound(
    dataset_version_id: str, object_count: int
) -> None:
    snapshot = DataSnapshotManifest(
        dataset_version_id=dataset_version_id,
        objects=tuple(
            DataObjectReference(sha256=f"hash-{index}", schema_id="daily_bar.v1", rows=index)
            for index in range(object_count)
        ),
        security_master_versions=("master-1",),
        mapping_versions=("mapping-1",),
        calendar_versions=("calendar-1",),
        factor_series_versions=("factor-1",),
        quality_rule_set_version="quality-1",
        quality_assessment_cutoff=datetime(2025, 1, 1, tzinfo=UTC),
    )
    first_id = data_snapshot_id(snapshot)
    second_id = data_snapshot_id(snapshot)

    changed = DataSnapshotManifest(
        dataset_version_id=dataset_version_id + "!",
        objects=snapshot.objects,
        security_master_versions=snapshot.security_master_versions,
        mapping_versions=snapshot.mapping_versions,
        calendar_versions=snapshot.calendar_versions,
        factor_series_versions=snapshot.factor_series_versions,
        quality_rule_set_version=snapshot.quality_rule_set_version,
        quality_assessment_cutoff=snapshot.quality_assessment_cutoff,
    )

    assert first_id == second_id
    assert first_id != data_snapshot_id(changed)
    assert first_id.startswith("sha256:")


def test_research_manifest_completeness() -> None:
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
        cost_model="cost-1",
        missing_price_policy="UNAVAILABLE",
        tradability_coverage="DAILY",
        deterministic_seed=0,
    )

    assert set(manifest.as_dict()) == {
        "run_id",
        "snapshot_id",
        "security_scope",
        "date_range",
        "providers",
        "calendar_versions",
        "adjustment_mode",
        "quality_rule_version",
        "research_logic_version",
        "parameters",
        "dependency_environment_id",
        "generated_at",
        "benchmark",
        "cost_model",
        "missing_price_policy",
        "tradability_coverage",
        "deterministic_seed",
    }
    assert canonical_json(manifest.as_dict()).count("\\u") == 0
