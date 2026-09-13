from __future__ import annotations

from pathlib import Path

import pyarrow as pa  # type: ignore[import-untyped]

from stock_platform.infrastructure.parquet.object_store import (
    ImmutableParquetObjectStore,
    ParquetStoreError,
)


class DatasetPublisher:
    """Publish one immutable object to a store for one dataset version."""

    def __init__(self, store: ImmutableParquetObjectStore) -> None:
        self._store = store

    def publish(
        self,
        schema: pa.Schema,
        rows: tuple[dict[str, object], ...],
        *,
        dataset_name: str = "daily_bar.v1",
    ) -> Path:
        try:
            return self._store.publish(schema, rows, dataset_name=dataset_name)
        except ParquetStoreError as error:
            raise error
