from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class ResearchSnapshot:
    """A persistent research record."""

    snapshot_id: str
    created_at: datetime
    source_run_id: str


@dataclass(frozen=True, slots=True)
class PendingKeyword:
    """A keyword that is observed as pending."""

    keyword: str

    @property
    def pending(self) -> tuple[str, ...]:
        return (self.keyword,)


def canonical_business_id(timestamp: datetime) -> str:
    """Produce a deterministic business identifier for run tracking."""
    value = timestamp.astimezone(UTC)
    return f"{value.strftime('%Y%m%dT%H:%M:%SZ')}"


def mean(values: Sequence[float]) -> float:
    """Calculate the arithmetic mean of a non-empty numeric sequence."""
    if not values:
        raise ValueError("values must not be empty")
    return sum(values) / len(values)
