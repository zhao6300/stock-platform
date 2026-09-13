from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class SeriesPoint:
    """Point value for a dated observation."""

    date: date
    value: Decimal | None


type MissingPoint = Decimal | None
