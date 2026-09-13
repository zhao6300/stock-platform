from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

StatusName = Literal[
    "platform",
    "adapter",
    "contract",
    "schema",
    "compatible_schemas",
    "storage",
    "latest_ingestion",
]


@dataclass(frozen=True, slots=True)
class StatusDiagnostics:
    """A complete local status readout used by every client surface."""

    installed: tuple[str, ...]
    adapter: str | None
    contract: str | None
    schema: str | None
    compatible_schemas: tuple[str, ...]
    storage: str | None
    latest_ingestion: str
    platform: str
