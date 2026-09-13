from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from types import MappingProxyType
from typing import Any
from uuid import UUID

from stock_platform.application.replay import replay_pinned_research
from stock_platform.domain.common import Failure, Success
from stock_platform.domain.research import (
    DataSnapshotManifest,
    ResearchDateRange,
    ResearchManifest,
)


def _manifest() -> ResearchManifest:
    return ResearchManifest(
        run_id=UUID("00000000-0000-7000-8000-000000000001"),
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


def _repositories() -> MappingProxyType[str, tuple[str, ...]]:
    return MappingProxyType(
        {
            "calendar": ("calendar-1",),
            "adjustment_mode": ("UNADJUSTED",),
            "quality_rule": ("quality-1",),
            "research_logic": ("logic-1",),
            "dependency_environment": ("environment-1",),
        }
    )


@dataclass
class _Runner:
    output: dict[str, Any]
    called: bool = False

    def replay(self, manifest: ResearchManifest) -> dict[str, Any]:
        self.called = True
        return self.output


def test_replays_exact_manifest_when_all_artifacts_are_pinned() -> None:
    runner = _Runner({"result": "CREATED"})
    result = replay_pinned_research(_manifest(), {"result": "CREATED"}, runner, _repositories(), _snapshot())

    assert isinstance(result, Success)
    assert result.value.differences == ()
    assert runner.called is True
    assert result.value.manifest_differences == ()


def test_collects_complete_absence_before_replaying() -> None:
    runner = _Runner({})
    result = replay_pinned_research(_manifest(), {}, runner, MappingProxyType({}), None)

    assert isinstance(result, Failure)
    assert tuple(item.kind for item in result.error.missing) == (
        "snapshot",
        "calendar",
        "adjustment_mode",
        "quality_rule",
        "research_logic",
        "dependency_environment",
    )
    assert runner.called is False
