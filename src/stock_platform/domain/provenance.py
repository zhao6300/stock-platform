from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

_PROVIDER_IDENTIFIER_LIMIT = 255


@dataclass(frozen=True, slots=True)
class ProviderProvenance:
    """Provenance retained through normalization and canonical persistence."""

    provider: str
    provider_identifiers: tuple[str, ...]
    source_version: str | None
    correlation_id: str | None
    retrieved_at: datetime

    def __post_init__(self) -> None:
        if not self.provider:
            raise ValueError("provider must not be blank")
        if not self.provider_identifiers:
            raise ValueError("provider_identifiers must not be empty")
        if any(
            not identifier or len(identifier) > _PROVIDER_IDENTIFIER_LIMIT
            for identifier in self.provider_identifiers
        ):
            raise ValueError("provider identifiers must contain 1 to 255 characters")
        if self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware")
