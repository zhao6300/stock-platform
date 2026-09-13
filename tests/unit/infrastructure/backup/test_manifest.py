from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from stock_platform.domain.common import Failure, Success
from stock_platform.infrastructure.backup.backup import (
    BackupPlatformState,
    default_backup_manifest,
)
from stock_platform.infrastructure.backup.manifest import (
    BackupManifest,
    DatasetManifest,
    restore_compatibility,
    restore_eligible,
    verify_dataset_directory,
)


def _dataset(
    path: Path, schema_id: str = "schema-v1", rows: int = 1, record: bytes = b"row"
) -> DatasetManifest:
    return DatasetManifest(
        name=path.name,
        schema_id=schema_id,
        rows=rows,
        sha256=sha256(record).hexdigest(),
        bytes=len(record),
    )


def test_restore_compatibility_requires_explicit_schema() -> None:
    path = Path("bars.parquet")
    dataset = _dataset(path)
    manifest = BackupManifest(schema_id=dataset.schema_id, datasets=(dataset,))

    accepted = restore_compatibility(manifest, (dataset.schema_id,))
    denied = restore_compatibility(manifest, ("schema-v2",))

    assert isinstance(accepted, Success)
    assert accepted.value == dataset.schema_id
    assert isinstance(denied, Failure)
    assert denied.error.expected_schema == dataset.schema_id
    assert denied.error.compatible_schemas == ("schema-v2",)


def test_verify_dataset_directory_requires_exact_counts_and_hashes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "bars.parquet"
    path.write_bytes(b"row")
    dataset = _dataset(path)
    manifest = BackupManifest(schema_id=dataset.schema_id, datasets=(dataset,))

    verified = verify_dataset_directory(manifest, tmp_path)
    invalid = verify_dataset_directory(
        BackupManifest(
            schema_id=dataset.schema_id,
            datasets=(
                DatasetManifest(
                    name=dataset.name,
                    schema_id=dataset.schema_id,
                    rows=1,
                    sha256="0" * 64,
                    bytes=dataset.bytes,
                ),
            ),
        ),
        tmp_path,
    )

    assert isinstance(verified, Success)
    assert isinstance(invalid, Failure)
    assert invalid.error.checksum_mismatch == (dataset.name,)


def test_restore_eligible_reports_incompatibility_before_artifact_read(
    tmp_path: Path,
) -> None:
    path = tmp_path / "bars.parquet"
    path.write_bytes(b"row")
    dataset = _dataset(path)
    manifest = BackupManifest(schema_id=dataset.schema_id, datasets=(dataset,))

    result = restore_eligible(manifest, ("schema-v2",), tmp_path)

    assert isinstance(result, Failure)
    assert result.error.expected_schema == dataset.schema_id


def test_default_backup_manifest_omits_plaintext_credentials() -> None:
    state = BackupPlatformState(
        schema_id="schema-v1",
        configuration=("config-v1",),
        security_master_versions=("master-v1",),
        security_mappings=("mapping-v1",),
        calendars=("calendar-v1",),
        retained_data=("bars-v1",),
        quality_reports=("quality-v1",),
        snapshot_ids=("snapshot-1",),
        manifests=("manifest-1",),
        research_results=("result-1",),
        credentials=("secret-token",),
    )

    manifest = default_backup_manifest(state)

    dataset_names = tuple(dataset.name for dataset in manifest.datasets)
    assert set(dataset_names) == {
        "configuration",
        "security_master_versions",
        "security_mappings",
        "calendars",
        "retained_data",
        "quality_reports",
        "snapshot_ids",
        "manifests",
        "research_results",
    }
    assert not any(dataset.name == "credentials" for dataset in manifest.datasets)
    assert not any("secret-token" in dataset.name for dataset in manifest.datasets)
