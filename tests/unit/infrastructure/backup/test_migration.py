from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from stock_platform.domain.common import Failure, Success
from stock_platform.infrastructure.backup.manifest import (
    BackupManifest,
    DatasetManifest,
)
from stock_platform.infrastructure.backup.migration import migration_eligible


def test_migration_requires_explicit_schema_and_verified_backup(tmp_path: Path) -> None:
    path = tmp_path / "bars.parquet"
    path.write_bytes(b"row")
    dataset = DatasetManifest(
        name=path.name,
        schema_id="schema-v1",
        rows=1,
        sha256=sha256(b"row").hexdigest(),
        bytes=len(b"row"),
    )
    manifest = BackupManifest(schema_id="schema-v1", datasets=(dataset,))

    eligible = migration_eligible(
        "schema-v1",
        "schema-v2",
        manifest,
        tmp_path,
        ("schema-v1", "schema-v2"),
    )

    assert isinstance(eligible, Success)
    assert eligible.value.plan.to_schema == "schema-v2"
    assert eligible.value.target_schema == "schema-v2"


def test_migration_rejects_same_schema_and_incompatible_target(tmp_path: Path) -> None:
    path = tmp_path / "bars.parquet"
    path.write_bytes(b"row")
    dataset = DatasetManifest(
        name=path.name,
        schema_id="schema-v1",
        rows=1,
        sha256=sha256(b"row").hexdigest(),
        bytes=len(b"row"),
    )
    manifest = BackupManifest(schema_id="schema-v1", datasets=(dataset,))

    same = migration_eligible(
        "schema-v1",
        "schema-v1",
        manifest,
        tmp_path,
        ("schema-v1",),
    )
    incompatible = migration_eligible(
        "schema-v1",
        "schema-v2",
        manifest,
        tmp_path,
        ("schema-v1",),
    )

    assert isinstance(same, Failure)
    assert same.error.incompatible
    assert isinstance(incompatible, Failure)
    assert incompatible.error.incompatible
