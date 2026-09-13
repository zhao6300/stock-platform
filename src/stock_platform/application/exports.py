from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from stock_platform.domain.compliance import ComplianceProfileVersion
from stock_platform.domain.exports import RetentionPermission

type ExportCategory = Literal[
    "RAW_PROVIDER_DATA",
    "NORMALIZED_PROVIDER_DATA",
    "DERIVED_RESULTS",
]

_PERMITTED_EXPORT_CATEGORIES: dict[ExportPermission, frozenset[ExportCategory]] = {
    "PROHIBITED": frozenset(),
    "DERIVED_RESULTS_ONLY": frozenset({"DERIVED_RESULTS"}),
    "NORMALIZED_PROVIDER_DATA": frozenset({"DERIVED_RESULTS", "NORMALIZED_PROVIDER_DATA"}),
    "RAW_PROVIDER_DATA": frozenset({"DERIVED_RESULTS", "NORMALIZED_PROVIDER_DATA", "RAW_PROVIDER_DATA"}),
}


@dataclass(frozen=True, slots=True)
class ExportAuthorization:
    """Decision object holding all required export context."""

    profile: ComplianceProfileVersion
    category: ExportCategory
    retention: RetentionPermission
    payload: str
    authorized: bool

    @property
    def payload_bytes(self) -> bytes | None:
        if not self.authorized:
            return None
        return self.payload.encode("utf-8")

    def as_dict(self) -> dict[str, object]:
        return {
            "profile": self.profile,
            "category": self.category,
            "retention": self.retention,
            "payload": self.payload,
            "authorized": self.authorized,
            "redacted": False,
        }


@dataclass(frozen=True, slots=True)
class ExportDenied:
    profile: ComplianceProfileVersion
    category: ExportCategory


@dataclass(frozen=True, slots=True)
class ExportRequest:
    profile: ComplianceProfileVersion
    category: ExportCategory
    payload: bytes

    @property
    def retention(self) -> RetentionPermission:
        return self.profile.retention_permission

    def as_dict(self) -> dict[str, object]:
        return {
            "profile": self.profile,
            "category": self.category,
            "payload_size": len(self.payload),
        }


def authorize_export(
    profile: ComplianceProfileVersion,
    category: ExportCategory,
) -> ExportAuthorization | ExportDenied:
    if category in _PERMITTED_EXPORT_CATEGORIES[profile.export_permission]:
        return ExportAuthorization(
            profile=profile,
            category=category,
            retention=profile.retention_permission,
            payload="",
            authorized=True,
        )
    return ExportDenied(profile=profile, category=category)
