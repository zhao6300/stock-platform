from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from stock_platform.application.status import StatusDiagnostics

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


@dataclass(frozen=True, slots=True)
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
        )
