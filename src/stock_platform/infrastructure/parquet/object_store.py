from __future__ import annotations

from hashlib import sha256
from json import dumps
from os import fsync
from pathlib import Path
from typing import Any

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]


class ParquetStoreError(Exception):
    """Raised when an immutable object cannot be read or published."""


class ImmutableParquetObjectStore:
    """Write immutable objects under SHA-256 paths and return the file path."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def publish(
        self,
        schema: pa.Schema,
        rows: tuple[dict[str, Any], ...],
        *,
        dataset_name: str = "daily_bar.v1",
    ) -> Path:
        table = pa.Table.from_pylist(list(rows), schema=schema)
        digest = sha256()
        digest.update(str(schema).encode("utf-8"))
        digest.update(
            sha256(
                dumps(
                    table.to_pylist(),
                    default=str,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).digest()
        )
        object_path = self.root / f"{digest.hexdigest()}--{dataset_name}.parquet"
        if object_path.exists():
            return object_path

        temporary_path = object_path.with_suffix(".tmp")
        pq.write_table(table, temporary_path)
        with temporary_path.open("rb") as temporary_file:
            fsync(temporary_file.fileno())
        temporary_path.replace(object_path)
        return object_path

    def read(self, path: Path) -> pa.Table:
        return pq.read_table(path)
