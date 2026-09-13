from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class AnnualizedVolatility:
    """Takes a Sequence[SeriesPoint] and returns a typed result."""

    values: Sequence[Decimal]

    @property
    def annualization_factor(self) -> Decimal:
        return Decimal("252")
