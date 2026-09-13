from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from stock_platform.application.publication import publish_dataset
from stock_platform.infrastructure.parquet.object_store import (
    ImmutableParquetObjectStore,
)
from stock_platform.infrastructure.parquet.publisher import DatasetPublisher
from stock_platform.infrastructure.parquet.schemas import DAILY_BAR_SCHEMA


def _rows() -> tuple[dict[str, object], ...]:
    return (
        {
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
        },
    )


def test_publish_dataset_writes_before_returning_the_sqlite_ref(
    tmp_path: Path,
) -> None:
    publisher = DatasetPublisher(ImmutableParquetObjectStore(tmp_path))
    rows = _rows()

    result = publish_dataset(publisher, DAILY_BAR_SCHEMA, rows)

    assert result is not None
    store = ImmutableParquetObjectStore(tmp_path)
    assert store.read(result.value).to_pylist() == list(rows)
