from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from stock_platform.infrastructure.backup.manifest import (
    BackupManifest,
    DatasetManifest,
)
from stock_platform.infrastructure.backup.restore import restore_backup


def test_restore_backs_up_and_verifies_target(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    path = source / "bars.parquet"
    path.write_bytes(b"row")
    dataset = DatasetManifest(
        name="bars.parquet",
        schema_id="schema-v1",
        rows=1,
        sha256=sha256(b"row").hexdigest(),
        bytes=len(b"row"),
    )
    manifest = BackupManifest(schema_id="schema-v1", datasets=(dataset,))

    restored = restore_backup(
        manifest,
        source,
        target,
        compatible_schemas=("schema-v1",),
    )

    assert restored == target
    assert (target / "bars.parquet").read_bytes() == b"row"


def test_restore_rejects_incompatible_schema(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    manifest = BackupManifest(schema_id="schema-v1", datasets=())

    with pytest.raises(ValueError):
        restore_backup(
            manifest,
            source,
            target,
            compatible_schemas=("schema-v2",),
        )
