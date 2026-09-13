from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from stock_platform.domain.common import Failure, Result, Success
from stock_platform.domain.research import (
    DataSnapshotManifest,
    MissingReplayArtifact,
    ResearchManifest,
    missing_replay_artifacts,
)


@dataclass(frozen=True, slots=True)
class ResearchRunOutcome:
    """One deterministic run result and its committed manifest."""

    manifest: ResearchManifest
    result: str


@dataclass(frozen=True, slots=True)
class ReplayOutcome:
    """A pinned-input replay result or the complete set of missing artifacts."""

    result: str | None
    missing: tuple[MissingReplayArtifact, ...]


class ResearchManifestRepository(Protocol):
    """The narrow port needed for manifest-before-result publication."""

    def save(self, manifest: ResearchManifest) -> Result[None, str]: ...

    def get(self, manifest_id: str) -> ResearchManifest | None: ...

    def run(self, manifest: ResearchManifest) -> Result[ResearchRunOutcome, str]: ...


class ResearchRunner:
    """Persist the run boundary before creating any derived research result."""

    def __init__(self, repositories: Mapping[str, Sequence[str]]) -> None:
        self._repositories = repositories

    def prepare(
        self,
        manifest: ResearchManifest,
        snapshot: DataSnapshotManifest | None,
    ) -> Result[ReplayOutcome, ReplayOutcome]:
        """Return the complete unavailable set or the pinned replay readiness."""
        missing = missing_replay_artifacts(manifest, snapshot, self._repositories)
        if missing:
            return Failure(ReplayOutcome(None, missing))
        return Success(ReplayOutcome("READY", ()))

    def apply_replay(
        self,
        runner: ResearchManifestRepository,
        manifest: ResearchManifest,
        snapshot: DataSnapshotManifest | None,
    ) -> Result[ResearchRunOutcome, ReplayOutcome]:
        """Run the replay runner using the pinned artifacts; fail atomically."""
        preparation = self.prepare(manifest, snapshot)
        if not isinstance(preparation, Success):
            return Failure(preparation.error)

        saved = runner.save(manifest)
        if not isinstance(saved, Success):
            return Failure(
                ReplayOutcome(None, (MissingReplayArtifact("manifest", saved.error),))
            )

        result = runner.run(manifest)
        if not isinstance(result, Success):
            return Failure(ReplayOutcome(None, (MissingReplayArtifact("result", result.error),)))
        return result

    def run(
        self,
        runner: ResearchManifestRepository,
        manifest: ResearchManifest,
    ) -> Result[ResearchRunOutcome, str]:
        """Commit the manifest, then publish exactly one derived result."""
        result = runner.run(manifest)
        if not isinstance(result, Success):
            return Failure(result.error)
        return result
