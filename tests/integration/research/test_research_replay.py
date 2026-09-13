from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from types import MappingProxyType
from uuid import UUID

import pytest

from stock_platform.application.container import ApplicationContainer
from stock_platform.application.research_runner import ResearchRunner, ResearchRunOutcome
from stock_platform.domain.common import Failure, Success
from stock_platform.domain.research import (
    DataObjectReference,
    DataSnapshotManifest,
    ResearchDateRange,
    ResearchManifest,
    replay_differences,
)


def _manifest() -> ResearchManifest:
    return ResearchManifest(
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


def _snapshot(objects: tuple[DataObjectReference, ...] = ()) -> DataSnapshotManifest:
    return DataSnapshotManifest(
        dataset_version_id="dataset-1",
        objects=objects,
        security_master_versions=("master-1",),
        mapping_versions=("mapping-1",),
        calendar_versions=("calendar-1",),
        factor_series_versions=("factor-1",),
        quality_rule_set_version="quality-1",
        quality_assessment_cutoff=datetime(2025, 1, 1, tzinfo=UTC),
    )


def _repositories() -> MappingProxyType:
    return MappingProxyType(
        {
            "calendar": ("calendar-1",),
            "adjustment_mode": ("UNADJUSTED",),
            "quality_rule": ("quality-1",),
            "research_logic": ("logic-1",),
            "dependency_environment": ("environment-1",),
        }
    )


class _FakeRepository:
    def __init__(self, save_error: str | None) -> None:
        self._save_error = save_error
        self.saved: list[ResearchManifest] = []
        self.ran: list[ResearchManifest] = []

    def save(self, manifest: ResearchManifest) -> Success | Failure:
        if self._save_error is not None:
            return Failure(self._save_error)
        self.saved.append(manifest)
        return Success(None)

    def run(self, manifest: ResearchManifest) -> Success | Failure:
        self.ran.append(manifest)
        return Success(ResearchRunOutcome(manifest=manifest, result="CREATED"))


def test_snapshot_confirmation_is_bound_to_pinned_id() -> None:
    container = ApplicationContainer()
    snapshot = _snapshot(objects=(DataObjectReference("hash", "daily_bar.v1", 1),))
    snapshot_id = container.create_snapshot(snapshot)

    confirmed = container.confirm_rejected_snapshot(snapshot_id)

    assert confirmed is True
    assert snapshot_id in container.snapshots
    assert snapshot_id in container.reject_confirmations
    with pytest.raises(LookupError):
        container.confirm_rejected_snapshot("unknown")


def test_research_replay_saves_manifest_before_result() -> None:
    repository = _FakeRepository(save_error=None)
    runner = ResearchRunner(_repositories())
    manifest = _manifest()

    outcome = runner.apply_replay(repository, manifest, _snapshot(objects=()))

    assert isinstance(outcome, Success)
    assert isinstance(outcome.value, ResearchRunOutcome)
    assert outcome.value.manifest == manifest
    assert outcome.value.result == "CREATED"
    assert repository.saved == [manifest]
    assert repository.ran == [manifest]

    missing = runner.prepare(manifest, None)
    assert isinstance(missing, Failure)
    assert missing.error.result is None
    assert tuple(item.kind for item in missing.error.missing) == ("snapshot",)


def test_research_replay_detects_numeric_and_manifest_differences() -> None:
    result = replay_differences(
        {"value": Decimal("1.0")},
        {"value": Decimal("1.0000000000001")},
    )
    assert result == ()

    difference = replay_differences(
        {"value": Decimal("1.0")},
        {"value": Decimal("2.0")},
    )
    assert tuple(item.field for item in difference) == ("value",)
