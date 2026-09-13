from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from stock_platform.domain.common import Failure, Result, Success
from stock_platform.domain.research import (
    DataSnapshotManifest,
    MissingReplayArtifact,
    ReplayDifference,
    ResearchManifest,
    manifest_diff,
    missing_replay_artifacts,
    replay_differences,
)


class ReplayRunner(Protocol):
    """The narrow pinned-input port used for deterministic replay."""

    def replay(self, manifest: ResearchManifest) -> Mapping[str, Any]: ...


@dataclass(frozen=True, slots=True)
class ReplayFailure:
    """A replay rejection carrying its complete set of empty artifacts."""

    missing: tuple[MissingReplayArtifact, ...]


@dataclass(frozen=True, slots=True)
class ReplayOutcome:
    """A deterministic replay result with its precise difference report."""

    manifest_differences: tuple[tuple[str, Any, Any], ...]
    differences: tuple[ReplayDifference, ...]


type ReplayResult = Result[ReplayOutcome, ReplayFailure]


def replay_pinned_research(
    manifest: ResearchManifest,
    original: Mapping[str, Any],
    runner: ReplayRunner,
    repositories: Mapping[str, Sequence[str]],
    snapshot: DataSnapshotManifest | None,
) -> ReplayResult:
    """Run pinned artifacts only, then compare all output paths exactly."""
    missing = missing_replay_artifacts(manifest, snapshot, repositories)
    if missing:
        return Failure(ReplayFailure(missing))

    replayed = runner.replay(manifest)
    return Success(
        ReplayOutcome(
            manifest_differences=manifest_diff(manifest, manifest),
            differences=replay_differences(original, replayed),
        )
    )
