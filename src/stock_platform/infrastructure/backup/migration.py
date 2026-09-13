from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from stock_platform.domain.common import Failure, Result, Success
from stock_platform.infrastructure.backup.manifest import (
    BackupManifest,
    verify_dataset_directory,
)


@dataclass(frozen=True, slots=True)
class MigrationPlan:
    """One schema/data-layout change with explicit restore-compatible scope."""

    from_schema: str
    to_schema: str
    started_at: datetime

    def compatible(self) -> bool:
        return self.from_schema != self.to_schema


@dataclass(frozen=True, slots=True)
class MigrationBlocked:
    """All gates required before any migration touches the platform."""

    incompatible: bool = False
    backup_not_restorable: bool = False
    no_backup: bool = True


@dataclass(frozen=True, slots=True)
class MigrationEligible:
    """A migration and its verified backup target."""

    plan: MigrationPlan
    target_schema: str


def migration_eligible(
    current_schema: str,
    target_schema: str,
    backup: BackupManifest,
    backup_directory: Path,
    compatible_schemas: tuple[str, ...],
) -> Result[MigrationEligible, MigrationBlocked]:
    """Gate on verified pre-migration backup and explicit schema targets."""
    if current_schema == target_schema:
        return Failure(MigrationBlocked(incompatible=True))
    if target_schema not in compatible_schemas:
        return Failure(MigrationBlocked(incompatible=True))
    verification = verify_dataset_directory(backup, backup_directory)
    if isinstance(verification, Failure):
        return Failure(MigrationBlocked(backup_not_restorable=True))
    plan = MigrationPlan(
        from_schema=current_schema,
        to_schema=target_schema,
        started_at=datetime.now(UTC),
    )
    if not plan.compatible():
        return Failure(MigrationBlocked(incompatible=True))
    return Success(MigrationEligible(plan=plan, target_schema=target_schema))
