from __future__ import annotations

from dataclasses import dataclass

from stock_platform.domain.research import (
    DataSnapshotManifest,
    SnapshotProjection,
    data_snapshot_id,
    project_snapshot,
)


@dataclass(frozen=True, slots=True)
class SnapshotSummary:
    """A complete projection of a pinned Data Snapshot and its digest."""

    manifest: DataSnapshotManifest
    snapshot_id: str
    projection: SnapshotProjection


def summarize_snapshot(snapshot: DataSnapshotManifest) -> SnapshotSummary:
    """Attach the content-bound snapshot ID to its existing manifest data."""
    projection = project_snapshot(snapshot)
    return SnapshotSummary(
        manifest=snapshot,
        snapshot_id=data_snapshot_id(snapshot),
        projection=projection,
    )
