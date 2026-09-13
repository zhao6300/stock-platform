from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

type ObservationPoint = date | Sequence[Decimal]


@dataclass(frozen=True, slots=True)
class Observation:
    """One dated observation, represented as a unique identifier."""

    date: date
    values: Sequence[Decimal]


def canonical_values(values: Sequence[Decimal]) -> Sequence[Decimal]:
    """Normalize values and drop explicit missing observations."""
    if not values:
        raise ValueError("values must not be empty")
    return sorted(values)
