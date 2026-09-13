from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from stock_platform.infrastructure.parquet.object_store import (
    ImmutableParquetObjectStore,
)
from stock_platform.infrastructure.parquet.schemas import (
    DAILY_BAR_SCHEMA,
    FUND_NAV_SCHEMA,
)


def test_immutable_object_store_round_trips_daily_and_fund_nav(
    tmp_path: Path,
) -> None:
    daily_row = {
        "canonical_security_id": "a-share:SH600000",
        "observation_date": date(2026, 1, 2),
        "open": Decimal("12.10"),
        "high": Decimal("12.50"),
        "low": Decimal("12.05"),
        "close": Decimal("12.38"),
        "volume": Decimal("120000"),
        "turnover": Decimal("1490000"),
        "currency": "CNY",
        "provider": "reference",
        "provider_identifier": "000000",
        "source_version": "v1",
        "retrieved_at": datetime(2026, 1, 2, 15, 0, tzinfo=UTC),
        "observation_version_id": "obs-1",
    }
    nav_row = {
        "canonical_security_id": "fund:000002",
        "observation_date": date(2026, 1, 2),
        "unit_nav": Decimal("1.23"),
        "cumulative_nav": Decimal("1.45"),
        "currency": "CNY",
        "provider": "reference",
        "provider_identifier": "000002",
        "source_version": "v1",
        "retrieved_at": datetime(2026, 1, 2, 15, 0, tzinfo=UTC),
        "observation_version_id": "obs-1",
    }
    store = ImmutableParquetObjectStore(tmp_path)

    daily_path = store.publish(DAILY_BAR_SCHEMA, (daily_row,))
    fund_path = store.publish(FUND_NAV_SCHEMA, (nav_row,), dataset_name="fund_nav.v1")

    daily_table = store.read(daily_path)
    fund_table = store.read(fund_path)
    assert daily_table.schema == DAILY_BAR_SCHEMA
    assert fund_table.schema == FUND_NAV_SCHEMA
    assert daily_table.to_pylist() == [daily_row]
    assert fund_table.to_pylist() == [nav_row]


def test_object_store_reuses_same_content_addressed_object(
    tmp_path: Path,
) -> None:
    store = ImmutableParquetObjectStore(tmp_path)
    publish = store.publish
    schema = DAILY_BAR_SCHEMA
    daily_row = {
        "canonical_security_id": "a-share:SH600000",
        "observation_date": date(2026, 1, 2),
        "open": Decimal("12.10"),
        "high": Decimal("12.50"),
        "low": Decimal("12.05"),
        "close": Decimal("12.38"),
        "volume": Decimal("120000"),
        "turnover": Decimal("1490000"),
        "currency": "CNY",
        "provider": "reference",
        "provider_identifier": "000000",
        "source_version": "v1",
        "retrieved_at": datetime(2026, 1, 2, 15, 0, tzinfo=UTC),
        "observation_version_id": "obs-1",
    }
    same_path1 = publish(schema, (daily_row,))
    same_path2 = publish(schema, (daily_row,))

    assert same_path1 == same_path2
    assert same_path1.exists()
