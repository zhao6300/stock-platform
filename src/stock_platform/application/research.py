from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from stock_platform.domain.research import canonical_business_id


@dataclass(frozen=True, slots=True)
class ResearchRequest:
    """A request record for a Research Run."""

    research_id: str
    snapshot_id: str
    created_at: datetime

    def business_id(self) -> str:
        return canonical_business_id(self.created_at)
