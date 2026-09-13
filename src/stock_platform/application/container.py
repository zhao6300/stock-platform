from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from stock_platform.application.backup import BackupPlatformState
from stock_platform.application.status import StatusDiagnostics
from stock_platform.domain.research import DataSnapshotManifest, data_snapshot_id

type ProviderName = str


@dataclass(frozen=True, slots=True)
class ContainerStatus:
    """A stable composition-root status readout."""

    installed: tuple[str, ...]
    adapter: str | None
    contract: str | None
    schema: str | None
    compatible_schemas: tuple[str, ...]
    storage: str | None
    latest_ingestion: str


@dataclass(slots=True)
class ApplicationContainer:
    """Hold the modules and state needed by application services."""

    providers: tuple[str, ...] = ()
    adapter: str | None = None
    contract: str | None = None
    schema: str | None = None
    compatible_schemas: tuple[str, ...] = ()
    storage: str | None = None
    latest_ingestion: str = "NO_SUCCESSFUL_INGESTION"
    catalog: Mapping[tuple[str, str], Sequence[Mapping[str, Any]]] = field(
        default_factory=dict
    )
    observations: dict[str, Any] = field(default_factory=dict)
    provider_configurations: dict[str, Mapping[str, Any]] = field(default_factory=dict)
    enabled_providers: frozenset[str] = frozenset()
    credential_references: frozenset[str] = frozenset()
    snapshots: dict[str, DataSnapshotManifest] = field(default_factory=dict)
    reject_confirmations: set[str] = field(default_factory=set)

    def status(self) -> StatusDiagnostics:
        """Return the summary diagnostics exposed through local APIs."""
        return StatusDiagnostics(
            installed=self.providers,
            adapter=self.adapter,
            contract=self.contract,
            schema=self.schema,
            compatible_schemas=self.compatible_schemas,
            storage=self.storage,
            latest_ingestion=self.latest_ingestion,
            platform="stock-research",
        )

    def configure_provider(
        self, provider: str, configuration: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        """Record one local provider configuration without transmitting secrets."""
        self.provider_configurations[provider] = dict(configuration)
        if provider not in self.providers:
            self.providers = (*self.providers, provider)
        return self.provider_configurations[provider]

    def enable_provider(
        self, provider: str, contract_version: str | None = None
    ) -> Mapping[str, Any]:
        """Mark one configured candidate active and pin its contract version."""
        if provider not in self.provider_configurations:
            raise LookupError(f"provider is not configured: {provider}")
        self.enabled_providers = frozenset((*self.enabled_providers, provider))
        if contract_version is not None:
            self.contract = contract_version
        return {"provider": provider, "enabled": True, "contract": contract_version}

    def create_snapshot(self, snapshot: DataSnapshotManifest) -> str:
        """Freeze one snapshot and return its canonical content-bound ID."""
        snapshot_id = data_snapshot_id(snapshot)
        self.snapshots[snapshot_id] = snapshot
        return snapshot_id

    def confirm_rejected_snapshot(self, snapshot_id: str) -> bool:
        """Record explicit confirmation only for a snapshot already pinned."""
        if snapshot_id not in self.snapshots:
            raise LookupError(f"snapshot is not pinned: {snapshot_id}")
        self.reject_confirmations.add(snapshot_id)
        return True

    def backup_platform_state(self) -> BackupPlatformState:
        """Build the local backup inventory source from current state."""
        return BackupPlatformState(
            schema_id=self.schema if self.schema is not None else "schema-v1",
            configuration=tuple(
                provider for provider in self.enabled_providers
            ),
            security_master_versions=(),
            security_mappings=(),
            calendars=(),
            retained_data=(),
            quality_reports=(),
            snapshot_ids=tuple(self.snapshots),
            manifests=(),
            research_results=(),
            credentials=tuple(self.credential_references),
        )
