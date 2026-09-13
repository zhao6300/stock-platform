from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from stock_platform.application.queries import QueryFilter, ResearchQuery
from stock_platform.client import open_snapshot
from stock_platform.domain.research import DataSnapshotManifest, data_snapshot_id


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


def test_open_snapshot_queries_through_application_layer() -> None:
    snapshot_id = data_snapshot_id(_snapshot())
    client = open_snapshot(
        snapshot_id,
        {(snapshot_id, "daily_bar"): ({"close": Decimal("10")},)},
    )

    result = client.query(
        ResearchQuery(
            entity="daily_bar",
            snapshot_id=snapshot_id,
            sort_field="close",
            filters=(QueryFilter("close", "10"),),
        )
    )

    assert result is not None
    assert result.value.rows[0] == (("close", "10"),)
