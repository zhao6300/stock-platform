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


@dataclass(frozen=True, slots=True)
class ExportAuthorization:
    """Decision object holding all required export context."""

    profile: ComplianceProfileVersion
    category: ExportCategory
    retention: RetentionPermission
    payload: str


@dataclass(frozen=True, slots=True)
class ExportRequest:
    profile: ComplianceProfileVersion
    category: ExportCategory
    payload: bytes
