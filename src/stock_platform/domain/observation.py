from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from stock_platform.domain.common import ensure_timezone_aware

type DomainCode = str


@dataclass(frozen=True, slots=True)
class ObservationCode:
    code: str
    kind: DomainCode


@dataclass(frozen=True, slots=True)
class Observation:
    code: ObservationCode
    provider: str
    retrieved_at: datetime
    dates: tuple[date, ...]

    @property
    def observation_date(self) -> date:
        """Return the effective date for a single-observation record."""
        return self.dates[0]

    def __post_init__(self) -> None:
        ensure_timezone_aware(self.retrieved_at)
        if not all(self.dates):
            raise ValueError("observation dates must not be empty")
        if len(self.dates) != len(set(self.dates)):
            raise ValueError("observation dates must be unique")
        if self.dates != tuple(sorted(self.dates)):
            raise ValueError("observation dates must be ordered")
