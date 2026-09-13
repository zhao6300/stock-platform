from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass

from stock_platform.domain.common import canonical_json
from stock_platform.infrastructure.backup.manifest import (
    BackupManifest,
    DatasetManifest,
)


@dataclass(frozen=True, slots=True)
class BackupPlatformState:
    """The exact platform state selected by a local default backup."""

    schema_id: str
    configuration: tuple[str, ...]
    security_master_versions: tuple[str, ...]
    security_mappings: tuple[str, ...]
    calendars: tuple[str, ...]
    retained_data: tuple[str, ...]
    quality_reports: tuple[str, ...]
    snapshot_ids: tuple[str, ...]
    manifests: tuple[str, ...]
    research_results: tuple[str, ...]
    credentials: tuple[str, ...] = ()


_REQUIRED_STATE_FIELDS = (
    "configuration",
    "security_master_versions",
    "security_mappings",
    "calendars",
    "retained_data",
    "quality_reports",
    "snapshot_ids",
    "manifests",
    "research_results",
)


def _dataset(name: str, values: tuple[str, ...]) -> DatasetManifest:
    return DatasetManifest(
        name=name,
        schema_id="platform-v1",
        rows=len(values),
        sha256=canonical_json(values),
        bytes=len(canonical_json(values)),
    )


def default_backup_manifest(state: BackupPlatformState) -> BackupManifest:
    """Return the required, secret-free default backup inventory."""
    datasets = tuple(_dataset(field, values) for field, values in _required_state_values(state))
    return BackupManifest(
        schema_id=state.get(
            "schema_id",
            "schema-v1",
        )
        if isinstance(state, Mapping)
        else state.schema_id,
        datasets=datasets,
    )


def _required_state_values(state: BackupPlatformState) -> Iterator[tuple[str, tuple[str, ...]]]:
    for field in _REQUIRED_STATE_FIELDS:
        values = state.get(field) if isinstance(state, Mapping) else getattr(state, field)
        if values is None:
            continue
        yield field, tuple(values)
