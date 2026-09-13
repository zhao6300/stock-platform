from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any
from uuid import UUID

from stock_platform.domain.common import canonical_json, ensure_timezone_aware

type JsonObject = dict[str, Any]


@dataclass(frozen=True, slots=True)
class DataObjectReference:
    """One immutable content-addressed artifact pinned by a snapshot."""

    sha256: str
    schema_id: str
    rows: int


@dataclass(frozen=True, slots=True)
class DataSnapshotManifest:
    """The complete immutable identity of a pinned data snapshot."""

    dataset_version_id: str
    objects: tuple[DataObjectReference, ...]
    security_master_versions: tuple[str, ...]
    mapping_versions: tuple[str, ...]
    calendar_versions: tuple[str, ...]
    factor_series_versions: tuple[str, ...]
    quality_rule_set_version: str
    quality_assessment_cutoff: datetime

    def __post_init__(self) -> None:
        ensure_timezone_aware(self.quality_assessment_cutoff)

    def as_dict(self) -> JsonObject:
        return {
            "dataset_version_id": self.dataset_version_id,
            "objects": [
                {"rows": item.rows, "schema_id": item.schema_id, "sha256": item.sha256}
                for item in self.objects
            ],
            "security_master_versions": list(self.security_master_versions),
            "mapping_versions": list(self.mapping_versions),
            "calendar_versions": list(self.calendar_versions),
            "factor_series_versions": list(self.factor_series_versions),
            "quality_rule_set_version": self.quality_rule_set_version,
            "quality_assessment_cutoff": canonical_json(self.quality_assessment_cutoff),
        }


def data_snapshot_id(snapshot: DataSnapshotManifest) -> str:
    """Return the canonical content-bound snapshot identifier."""
    digest = sha256(canonical_json(snapshot.as_dict()).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


@dataclass(frozen=True, slots=True)
class ResearchDateRange:
    """The inclusive date scope of one reproducible run."""

    start: date
    end: date


@dataclass(frozen=True, slots=True)
class ResearchManifest:
    """Every versioned input required by research replay."""

    run_id: UUID
    snapshot_id: str
    security_scope: tuple[str, ...]
    date_range: ResearchDateRange
    providers: tuple[str, ...]
    calendar_versions: tuple[str, ...]
    adjustment_mode: str
    quality_rule_version: str
    research_logic_version: str
    parameters: tuple[tuple[str, str], ...]
    dependency_environment_id: str
    generated_at: datetime
    benchmark: str | None
    cost_model: str
    missing_price_policy: str
    tradability_coverage: str
    deterministic_seed: int

    def __post_init__(self) -> None:
        ensure_timezone_aware(self.generated_at)

    def as_dict(self) -> JsonObject:
        return {
            "run_id": str(self.run_id),
            "snapshot_id": self.snapshot_id,
            "security_scope": list(self.security_scope),
            "date_range": {
                "start": canonical_json(self.date_range.start),
                "end": canonical_json(self.date_range.end),
            },
            "providers": list(self.providers),
            "calendar_versions": list(self.calendar_versions),
            "adjustment_mode": self.adjustment_mode,
            "quality_rule_version": self.quality_rule_version,
            "research_logic_version": self.research_logic_version,
            "parameters": [{"name": name, "value": value} for name, value in self.parameters],
            "dependency_environment_id": self.dependency_environment_id,
            "generated_at": canonical_json(self.generated_at),
            "benchmark": self.benchmark,
            "cost_model": self.cost_model,
            "missing_price_policy": self.missing_price_policy,
            "tradability_coverage": self.tradability_coverage,
            "deterministic_seed": self.deterministic_seed,
        }


@dataclass(frozen=True, slots=True)
class MissingReplayArtifact:
    """One unavailable pinned artifact or recorded version."""

    kind: str
    index: str | None = None


type ReplayInput = dict[str, Any]


@dataclass(frozen=True, slots=True)
class SnapshotProjection:
    """The read-only value that a data snapshot expresses in observability."""

    manifest: DataSnapshotManifest | None
    dataset_version_id: str | None
    calendar_versions: tuple[str, ...]


def project_snapshot(snapshot: DataSnapshotManifest | None) -> SnapshotProjection:
    """Return the simple manifest projection without inventing dataset rows."""
    if snapshot is None:
        return SnapshotProjection(
            manifest=None,
            dataset_version_id=None,
            calendar_versions=(),
        )
    return SnapshotProjection(
        manifest=snapshot,
        dataset_version_id=snapshot.dataset_version_id,
        calendar_versions=snapshot.calendar_versions,
    )


def missing_replay_artifacts(
    manifest: ResearchManifest,
    snapshot: DataSnapshotManifest | None,
    repositories: Mapping[str, Sequence[str]],
) -> tuple[MissingReplayArtifact, ...]:
    """Collect every absent pinned input before executing a replay."""
    missing: list[MissingReplayArtifact] = []
    if snapshot is None:
        missing.append(MissingReplayArtifact("snapshot", manifest.snapshot_id))
    manifest_dict = manifest.as_dict()
    records = {
        "calendar": list(manifest_dict["calendar_versions"]),
        "adjustment_mode": [manifest_dict["adjustment_mode"]],
        "quality_rule": [manifest_dict["quality_rule_version"]],
        "research_logic": [manifest_dict["research_logic_version"]],
        "dependency_environment": [manifest_dict["dependency_environment_id"]],
    }
    for kind, versions in records.items():
        available = set(repositories.get(kind, ()))
        missing.extend(
            MissingReplayArtifact(kind, version) for version in versions if version not in available
        )
    return tuple(missing)


def manifest_diff(
    left: ResearchManifest, right: ResearchManifest
) -> tuple[tuple[str, Any, Any], ...]:
    """Compare two manifests and return exactly their differing field values."""
    left_dict = left.as_dict()
    right_dict = right.as_dict()
    paths = sorted(set(left_dict) | set(right_dict))
    return tuple(
        (path, left_dict[path], right_dict[path])
        for path in paths
        if left_dict[path] != right_dict[path]
    )


@dataclass(frozen=True, slots=True)
class ReplayDifference:
    """One replay output or parameter that differs after the exact/tolerance rule."""

    field: str
    original: Any
    replayed: Any


def replay_differences(
    original: Mapping[str, Any], replayed: Mapping[str, Any]
) -> tuple[ReplayDifference, ...]:
    """Return every replay difference using discrete exact and numeric tolerance."""
    paths = sorted(set(original) | set(replayed))
    differences: list[ReplayDifference] = []
    for path in paths:
        left = original.get(path)
        right = replayed.get(path)
        equal = left == right
        if (
            not equal
            and isinstance(left, (int, float, Decimal))
            and isinstance(right, (int, float, Decimal))
        ):
            tolerance = Decimal("1e-10") * Decimal(max(1, abs(float(left))))
            equal = abs(Decimal(float(left)) - Decimal(float(right))) <= tolerance
        if not equal:
            differences.append(ReplayDifference(path, left, right))
    return tuple(differences)


def canonical_business_id(timestamp: datetime) -> str:
    """Produce a deterministic business identifier for run tracking."""
    value = timestamp.astimezone(UTC)
    return value.strftime("%Y%m%dT%H:%M:%SZ")
