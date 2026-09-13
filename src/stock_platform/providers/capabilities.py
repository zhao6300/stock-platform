from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

type MarketInstrumentPair = tuple[str, str]
type ProbeOutcome = Literal["success", "failure"]


class CapabilityReporter(Protocol):
    """Capability values assembled from provider responses."""

    def capability(
        self, name: str, value: Any
    ) -> CapabilityValue: ...

    def unreported(
        self, name: str
    ) -> CapabilityValue: ...


@dataclass(frozen=True, slots=True)
class CapabilityValue:
    rational_type: str
    rational_value: (
        tuple[str, ...]
        | tuple[
            MarketInstrumentPair,
            ...,
        ]
        | Literal[
            "empty",
            "unknown",
        ]
        | None
    )
    reported: bool


@dataclass(frozen=True, slots=True)
class CapabilityProbe:
    outcome: ProbeOutcome
    unsupported: tuple[MarketInstrumentPair, ...]


@dataclass(frozen=True, slots=True)
class ProviderReplacement:
    previous_adapter: str
    next_adapter: str
    probe: CapabilityProbe
