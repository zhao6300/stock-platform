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

    def run(
        self,
        runner: ResearchManifestRepository,
        manifest: ResearchManifest,
    ) -> Result[ResearchRunOutcome, str]:
        """Commit the manifest, then publish exactly one derived result."""
        saved = runner.save(manifest)
        if not isinstance(saved, Success):
            return Failure(saved.error)
        return Success(ResearchRunOutcome(manifest, "CREATED"))
