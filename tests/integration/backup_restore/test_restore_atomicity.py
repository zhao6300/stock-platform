from __future__ import annotations

from pathlib import Path

import pytest

from stock_platform.infrastructure.backup.manifest import BackupManifest, DatasetManifest
from stock_platform.infrastructure.backup.restore import restore_backup


def test_restore_preserves_existing_target_when_passed_incompatible_schema(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    target_file = target / "existing.txt"
    target_file.write_text("A")

    with pytest.raises(ValueError):
        restore_backup(
            BackupManifest(
                schema_id="schema-v1",
                datasets=(
                    DatasetManifest(
                        name="essential.txt",
                        schema_id="schema-v1",
                        rows=1,
                        sha256="invalid-checksum",
                        bytes=0,
                    ),
                ),
            ),
            source,
            target,
            compatible_schemas=("schema-v1",),
        )

    assert target_file.read_text() == "A"
