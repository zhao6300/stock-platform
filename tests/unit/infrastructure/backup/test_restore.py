from __future__ import annotations

from pathlib import Path

import pytest

from stock_platform.infrastructure.backup.manifest import BackupManifest
from stock_platform.infrastructure.backup.restore import restore_backup


def test_restore_requires_compatible_schema(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    manifest = BackupManifest(schema_id="schema-v1", datasets=())

    with pytest.raises(ValueError):
        restore_backup(
            manifest,
            source,
            tmp_path / "target",
            compatible_schemas=("schema-v2",),
        )
