from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from stock_platform.domain.common import Failure, Result, Success


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    """One expected immutable backup artifact."""

    name: str
    schema_id: str
    rows: int
    sha256: str
    bytes: int


@dataclass(frozen=True, slots=True)
class BackupManifest:
    """The complete required backup inventory, without credential secrets."""

    schema_id: str
    datasets: tuple[DatasetManifest, ...]

    def as_dict(self) -> dict[str, str | int | tuple[tuple[str, int, str], ...]]:
        return {
            "schema_id": self.schema_id,
            "datasets": tuple(
                (dataset.name, dataset.rows, dataset.sha256) for dataset in self.datasets
            ),
        }


@dataclass(frozen=True, slots=True)
class RestoreIncompatible:
    """Exact local restore compatibility failure."""

    expected_schema: str
    compatible_schemas: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RestoreVerificationFailure:
    """Exact count/checksum failures, independent of path order."""

    missing: tuple[str, ...] = ()
    count_mismatch: tuple[str, ...] = ()
    checksum_mismatch: tuple[str, ...] = ()


def restore_compatibility(
    manifest: BackupManifest,
    compatible_schemas: tuple[str, ...],
) -> Result[str, RestoreIncompatible]:
    """Accept only explicit restore-compatible schema versions."""
    if manifest.schema_id not in compatible_schemas:
        return Failure(
            RestoreIncompatible(
                expected_schema=manifest.schema_id,
                compatible_schemas=compatible_schemas,
            )
        )
    return Success(manifest.schema_id)


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(32768), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_dataset_directory(
    manifest: BackupManifest, directory: Path
) -> Result[str, RestoreVerificationFailure]:
    """Verify every required dataset count and content hash by independent read."""
    missing_names: list[str] = []
    bad_counts: list[str] = []
    bad_checksums: list[str] = []
    for dataset in manifest.datasets:
        path = directory / dataset.name
        if not path.exists():
            missing_names.append(dataset.name)
            continue
        if path.stat().st_size != dataset.bytes:
            bad_counts.append(dataset.name)
        if _sha256(path) != dataset.sha256:
            bad_checksums.append(dataset.name)

    if missing_names or bad_counts or bad_checksums:
        return Failure(
            RestoreVerificationFailure(
                missing=tuple(missing_names),
                count_mismatch=tuple(bad_counts),
                checksum_mismatch=tuple(bad_checksums),
            )
        )
    return Success(manifest.schema_id)


def restore_eligible(
    manifest: BackupManifest,
    compatible_schemas: tuple[str, ...],
    directory: Path,
) -> Result[str, RestoreVerificationFailure | RestoreIncompatible]:
    """Gate on compatibility first, then verify every artifact."""
    compatibility = restore_compatibility(manifest, compatible_schemas)
    if isinstance(compatibility, Failure):
        return compatibility
    verification = verify_dataset_directory(manifest, directory)
    if isinstance(verification, Failure):
        return verification
    return compatibility
