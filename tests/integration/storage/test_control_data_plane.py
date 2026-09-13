from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from stock_platform.application.publication import publish_dataset
from stock_platform.infrastructure.parquet.object_store import (
    ImmutableParquetObjectStore,
)
from stock_platform.infrastructure.parquet.publisher import DatasetPublisher
from stock_platform.infrastructure.parquet.schemas import DAILY_BAR_SCHEMA
from stock_platform.infrastructure.sqlite.models import (
    DatasetObjectRef,
    DatasetVersion,
    Provider,
)
from stock_platform.infrastructure.sqlite.unit_of_work import SQLiteUnitOfWork


def _daily_bar_rows() -> tuple[dict[str, object], ...]:
    return (
        {
            "canonical_security_id": "CN:A_Share:600000",
            "observation_date": date(2024, 1, 2),
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
            "retrieved_at": datetime(2024, 1, 2, 15, 0, tzinfo=UTC),
            "observation_version_id": "obs-1",
        },
    )


def test_control_data_plane_round_trip_rollback_and_append_only(tmp_path: Path) -> None:
    object_path = publish_dataset(
        DatasetPublisher(ImmutableParquetObjectStore(tmp_path / "objects")),
        DAILY_BAR_SCHEMA,
        _daily_bar_rows(),
    ).value
    object_content = object_path.read_bytes()
    object_hash = sha256(object_content).hexdigest()
    unit = SQLiteUnitOfWork(f"sqlite:///{tmp_path / 'control.sqlite3'}")

    with unit.begin() as session:
        provider = Provider(name="reference", created_at=date(2024, 1, 1))
        session.add(provider)
        session.flush()
        dataset = DatasetVersion(
            version_id="dataset-v1",
            parent_dataset="daily_bar.v1",
            manifest_hash=sha256(b'{"dataset":"daily_bar.v1","rows":1}').hexdigest(),
            row_count=1,
            schema_id="daily_bar.v1",
            created_at=date.today(),
        )
        session.add(dataset)
        session.flush()
        session.add(
            DatasetObjectRef(
                dataset_version_id=dataset.id,
                object_hash=object_hash,
                row_count=1,
                checksum=object_hash,
            )
        )

    with unit.begin() as session:
        dataset = session.get(DatasetVersion, 1)
        assert dataset is not None
        reference = session.get(DatasetObjectRef, 1)
        assert reference is not None
        assert reference.object_hash == object_hash
        candidate = session.scalars(
            select(DatasetObjectRef).where(
                DatasetObjectRef.dataset_version_id == 1,
                DatasetObjectRef.object_hash == object_hash,
            )
        ).all()
        assert len(candidate) == 1

    with pytest.raises(IntegrityError), unit.begin() as session:
        session.add(
            DatasetVersion(
                version_id="dataset-v1",
                parent_dataset="daily_bar.v1",
                manifest_hash=sha256(
                    b'{"dataset":"daily_bar.v1","rows":1}',
                ).hexdigest(),
                row_count=1,
                schema_id="daily_bar.v1",
                created_at=date.today(),
            )
        )

    with unit.begin() as session:
        assert session.get(DatasetVersion, 1) is not None
