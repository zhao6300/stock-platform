from __future__ import annotations

import shutil
from pathlib import Path

from stock_platform.domain.common import Failure
from stock_platform.infrastructure.backup.manifest import (
    BackupManifest,
    restore_compatibility,
    verify_dataset_directory,
)


def restore_backup(
    manifest: BackupManifest,
    source_directory: Path,
    target_directory: Path,
    *,
    compatible_schemas: tuple[str, ...],
) -> Path:
    """Copy a verified backup into target; remove artifacts if any step fails."""
    compatibility = restore_compatibility(manifest, compatible_schemas)
    if isinstance(compatibility, Failure):
        raise ValueError(f"schema is not restore-compatible: {compatibility.error}")
    preflight = verify_dataset_directory(manifest, source_directory)
    if isinstance(preflight, Failure):
        raise ValueError("backup artifacts are not restorable")

    if target_directory.exists():
        shutil.rmtree(target_directory)
    target_directory.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copytree(source_directory, target_directory, dirs_exist_ok=True)
        verification = verify_dataset_directory(manifest, target_directory)
        if isinstance(verification, Failure):
            raise ValueError("restored artifacts are not restorable")
    except Exception:
        shutil.rmtree(target_directory, ignore_errors=True)
        raise
    return target_directory
