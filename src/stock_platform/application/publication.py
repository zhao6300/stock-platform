from __future__ import annotations

from pathlib import Path

import pyarrow as pa  # type: ignore[import-untyped]

from stock_platform.domain.common import Result, Success
from stock_platform.domain.ingestion import IngestionRangeError
from stock_platform.infrastructure.parquet.publisher import DatasetPublisher


def publish_dataset(
    publisher: DatasetPublisher,
    schema: pa.Schema,
    rows: tuple[dict[str, object], ...],
    *,
    dataset_name: str = "daily_bar.v1",
) -> Result[Path, IngestionRangeError]:
    """Publish one object before any SQLite reference is opened."""
    return Success(publisher.publish(schema, rows, dataset_name=dataset_name))
