from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass

from stock_platform.domain.common import JsonObject, canonical_value


@dataclass(frozen=True, slots=True)
class DTO:
    """Base class for immutable application values with canonical output."""

    def as_dict(self) -> JsonObject:
        if not is_dataclass(self):
            raise TypeError("DTO subclasses must be dataclasses")
        return {field.name: canonical_value(getattr(self, field.name)) for field in fields(self)}
