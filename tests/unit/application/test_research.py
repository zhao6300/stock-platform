from __future__ import annotations

from datetime import UTC, date, datetime
from types import MappingProxyType
from uuid import UUID

from stock_platform.application.research import ResearchRequest
from stock_platform.application.research_runner import ResearchRunner
from stock_platform.domain.research import DataSnapshotManifest, ResearchDateRange, ResearchManifest


def test_research_id_is_canonical() -> None:
    value = ResearchRequest("222", "snap-1", datetime(2026, 1, 1, 12, 0, tzinfo=UTC))

    assert value.business_id() == "20260101T12:00:00Z"


def test_research_runner_preparates_without_missing() -> None:
    manifest = ResearchManifest(
        run_id=UUID("00000000-0000-7000-8000-000000000000"),
        snapshot_id="snapshot-1",
        security_scope=("security-1",),
        date_range=ResearchDateRange(start=date(2025, 1, 1), end=date(2025, 1, 2)),
        providers=("provider-1",),
        calendar_versions=("calendar-1", "calendar-2"),
        adjustment_mode="UNADJUSTED",
        quality_rule_version="quality-1",
        research_logic_version="logic-1",
        parameters=(("window", "10"),),
        dependency_environment_id="environment-1",
        generated_at=datetime(2025, 1, 1, tzinfo=UTC),
        benchmark="benchmark-1",
        cost_model="cost-1",
        missing_price_policy="UNAVAILABLE",
        tradability_coverage="DAILY",
        deterministic_seed=0,
    )
    snapshot = DataSnapshotManifest(
        dataset_version_id="dataset-1",
        objects=(),
        security_master_versions=("master-1",),
        mapping_versions=("mapping-1",),
        calendar_versions=("calendar-1", "calendar-2"),
        factor_series_versions=("factor-1",),
        quality_rule_set_version="quality-1",
        quality_assessment_cutoff=datetime(2025, 1, 1, tzinfo=UTC),
    )

    result = ResearchRunner(
        MappingProxyType(
            {
                "calendar": ("calendar-1", "calendar-2"),
                "adjustment_mode": ("UNADJUSTED",),
                "quality_rule": ("quality-1",),
                "research_logic": ("logic-1",),
                "dependency_environment": ("environment-1",),
            }
        )
    ).prepare(manifest, snapshot)

    assert result is not None
    assert len(result.value.missing) == 0
