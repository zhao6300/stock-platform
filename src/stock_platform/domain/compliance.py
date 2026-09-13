from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Literal

from stock_platform.domain.common import Failure, Result, Success


class AccountType(StrEnum):
    FREE = "FREE"
    TRIAL = "TRIAL"
    PAID_PERSONAL = "PAID_PERSONAL"
    PAID_PROFESSIONAL = "PAID_PROFESSIONAL"
    INSTITUTIONAL = "INSTITUTIONAL"


type PermittedPurpose = Literal[
    "PERSONAL_RESEARCH",
    "ACADEMIC_RESEARCH",
    "COMMERCIAL_RESEARCH",
    "REDISTRIBUTION",
]


type RetentionPermission = Literal[
    "PROHIBITED",
    "NORMALIZED_PROVIDER_DATA",
    "RAW_AND_NORMALIZED_PROVIDER_DATA",
]


type ExportPermission = Literal[
    "PROHIBITED",
    "DERIVED_RESULTS_ONLY",
    "NORMALIZED_PROVIDER_DATA",
    "RAW_PROVIDER_DATA",
]

_MAX_PROVIDER_NAME_LENGTH = 128
_MAX_DATA_SOURCE_LENGTH = 512
_MAX_PURPOSES = 4
_MINIMUM_OFFSET = timedelta(hours=-12)
_MAXIMUM_OFFSET = timedelta(hours=14)
_PERMITTED_PURPOSES = frozenset(
    (
        "PERSONAL_RESEARCH",
        "ACADEMIC_RESEARCH",
        "COMMERCIAL_RESEARCH",
        "REDISTRIBUTION",
    ),
)
_PERMITTED_RETENTION = frozenset(
    (
        "PROHIBITED",
        "NORMALIZED_PROVIDER_DATA",
        "RAW_AND_NORMALIZED_PROVIDER_DATA",
    ),
)
_PERMITTED_EXPORT = frozenset(
    (
        "PROHIBITED",
        "DERIVED_RESULTS_ONLY",
        "NORMALIZED_PROVIDER_DATA",
        "RAW_PROVIDER_DATA",
    ),
)
_EXPORT_PERMISSIONS = frozenset(
    (
        "PROHIBITED",
        "DERIVED_RESULTS_ONLY",
        "NORMALIZED_PROVIDER_DATA",
        "RAW_PROVIDER_DATA",
    ),
)
_ACCOUNT_TYPES = frozenset({item.value for item in AccountType})


@dataclass(frozen=True, slots=True)
class ComplianceCode:
    """A placeholder for future typed provider codes."""

    role: str
    target: str
    status: str


@dataclass(frozen=True, slots=True)
class ComplianceProfileVersion:
    """Versioned provider/l licence state."""

    profile_id: str
    provider_name: str
    data_source: str
    account_type: AccountType
    permitted_purposes: tuple[PermittedPurpose, ...]
    retention_permission: RetentionPermission
    export_permission: ExportPermission
    confirmation_time: datetime


@dataclass(frozen=True, slots=True)
class ComplianceValidationFailure:
    profile_id: str
    fields: frozenset[str]


@dataclass(frozen=True, slots=True)
class RetainedRawResponse:
    provider: str
    request_parameters: Mapping[str, str]
    profile: ComplianceProfileVersion
    request_time: datetime


@dataclass(frozen=True, slots=True)
class ComplianceProfile:
    profile_id: str
    version: ComplianceProfileVersion


class ComplianceHistory:
    """Append-only version registry for immutable compliance profiles."""

    def __init__(self) -> None:
        self._versions: list[ComplianceProfileVersion] = []

    def append(self, profile: ComplianceProfileVersion) -> ComplianceProfile:
        self._versions.append(profile)
        return ComplianceProfile(profile_id=profile.profile_id, version=profile)

    def profile_history(self) -> tuple[ComplianceProfile, ...]:
        return tuple(
            ComplianceProfile(profile_id=profile.profile_id, version=profile)
            for profile in self._versions
        )


class ComplianceValidator:
    """Validates the exact legal profile state required by the MVP boundary."""

    @classmethod
    def validate(
        cls, profile: ComplianceProfileVersion
    ) -> Result[ComplianceProfile, ComplianceValidationFailure]:
        invalid_fields = _invalid_profile_fields(profile)
        if invalid_fields:
            return Failure(
                ComplianceValidationFailure(
                    profile_id=profile.profile_id,
                    fields=invalid_fields,
                )
            )
        return Success(ComplianceProfile(profile_id=profile.profile_id, version=profile))


def _invalid_profile_fields(profile: ComplianceProfileVersion) -> frozenset[str]:
    invalid: set[str] = set()
    if not 1 <= len(profile.provider_name) <= _MAX_PROVIDER_NAME_LENGTH:
        invalid.add("provider_name")
    if not 1 <= len(profile.data_source) <= _MAX_DATA_SOURCE_LENGTH:
        invalid.add("data_source")
    if not profile.permitted_purposes or not len(profile.permitted_purposes) <= _MAX_PURPOSES:
        invalid.add("permitted_purposes")
    if len(profile.permitted_purposes) != len(set(profile.permitted_purposes)):
        invalid.add("permitted_purposes")
    if any(purpose not in _PERMITTED_PURPOSES for purpose in profile.permitted_purposes):
        invalid.add("permitted_purposes")
    if profile.account_type.value not in _ACCOUNT_TYPES:
        invalid.add("account_type")
    if profile.retention_permission not in _PERMITTED_RETENTION:
        invalid.add("retention_permission")
    if profile.export_permission not in _EXPORT_PERMISSIONS:
        invalid.add("export_permission")
    if not _is_legal_confirmation_time(profile.confirmation_time):
        invalid.add("confirmation_time")
    return frozenset(invalid)


def _is_legal_confirmation_time(timestamp: datetime) -> bool:
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        return False
    if timestamp.microsecond:
        return False
    offset = timestamp.utcoffset()
    if offset is None:
        return False
    if not _MINIMUM_OFFSET <= offset <= _MAXIMUM_OFFSET:
        return False
    return offset.total_seconds() % 60 == 0
