from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from stock_platform.application.snapshots import summarize_snapshot
from stock_platform.domain.research import DataSnapshotManifest


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


def test_summarize_snapshot_uses_content_bound_id() -> None:
    snapshot = _snapshot()

    first = summarize_snapshot(snapshot)
    second = summarize_snapshot(snapshot)

    assert first.snapshot_id == second.snapshot_id
    assert first.manifest is snapshot
    assert first.projection.manifest is snapshot
    assert first.projection.dataset_version_id == snapshot.dataset_version_id
    assert first.projection.calendar_versions == snapshot.calendar_versions


def test_summarize_snapshot_snapshot_id_encodes_content() -> None:
    snapshot = _snapshot()
    changed = _snapshot()
    changed = replace(changed, dataset_version_id="dataset-2")

    projection = summarize_snapshot(snapshot)
    changed_projection = summarize_snapshot(changed)

    assert projection.snapshot_id != changed_projection.snapshot_id
    assert projection.snapshot_id == summarize_snapshot(snapshot).snapshot_id
    assert changed_projection.snapshot_id == summarize_snapshot(changed).snapshot_id
