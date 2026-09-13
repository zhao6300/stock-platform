from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from stock_platform.domain.research import ResearchDateRange, ResearchManifest, manifest_diff


def _manifest(
    *,
    snapshot_id: str = "snapshot-1",
    adjustment_mode: str = "UNADJUSTED",
    quality_rule_version: str = "quality-1",
    deterministic_seed: int = 0,
) -> ResearchManifest:
    return ResearchManifest(
        run_id=UUID("00000000-0000-7000-8000-000000000001"),
        snapshot_id=snapshot_id,
        security_scope=("security-1",),
        date_range=ResearchDateRange(start=date(2025, 1, 1), end=date(2025, 1, 2)),
        providers=("provider-1",),
        calendar_versions=("calendar-1",),
        adjustment_mode=adjustment_mode,
        quality_rule_version=quality_rule_version,
        research_logic_version="logic-1",
        parameters=(("window", "10"),),
        dependency_environment_id="environment-1",
        generated_at=datetime(2025, 1, 2, tzinfo=UTC),
        benchmark="benchmark-1",
        cost_model="NONE",
        missing_price_policy="UNAVAILABLE",
        tradability_coverage="DAILY",
        deterministic_seed=deterministic_seed,
    )


def test_manifest_diff_reports_exact_fields() -> None:
    left = _manifest()
    right = _manifest(
        snapshot_id="snapshot-2",
        adjustment_mode="FORWARD_ADJUSTED",
        deterministic_seed=1,
    )

    differences = manifest_diff(left, right)

    assert tuple(item[0] for item in differences) == (
        "adjustment_mode",
        "deterministic_seed",
        "snapshot_id",
    )


def test_manifest_diff_reports_same_fields_unchanged() -> None:
    manifest = _manifest()

    differences = manifest_diff(manifest, manifest)

    assert differences == ()
