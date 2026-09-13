from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from stock_platform.domain.common import Failure, Result, Success
from stock_platform.domain.compliance import ComplianceProfileVersion
from stock_platform.domain.ingestion import (
    IngestionPlan,
    IngestionRangeError,
    PreflightError,
    planned_ingestion_dates,
    storage_preflight,
)


@dataclass(frozen=True, slots=True)
class IngestionPreflightRequest:
    """The bounded inputs needed by one complete local preflight gate."""

    expected_dates: Sequence[date]
    existing_dates: Sequence[date]
    start: date
    end: date
    refresh: bool
    compliance_profile: ComplianceProfileVersion
    credentials: Mapping[str, bool]
    storage_estimate: int
    storage_available: int


@dataclass(frozen=True, slots=True)
class IngestionPreflight:
    """All-or-nothing evidence needed before a provider network call."""

    plan: IngestionPlan
    allowed_provider_dates: tuple[date, ...]


@dataclass(frozen=True, slots=True)
class IngestionPreflightError:
    """Exact reason for each rejected local pre-network check."""

    range_error: IngestionRangeError | None = None
    compliance_denial: str | None = None
    credential_denial: str | None = None
    storage_error: PreflightError | None = None


def _compliance_denial(profile: ComplianceProfileVersion) -> str | None:
    if profile.retention_permission == "PROHIBITED":
        return "retention_permission"
    if profile.export_permission == "PROHIBITED":
        return "export_permission"
    return None


def ingestion_preflight(
    request: IngestionPreflightRequest,
) -> Result[IngestionPreflight, IngestionPreflightError]:
    """Gather every check required before contacting a provider."""
    plan_result = planned_ingestion_dates(
        request.expected_dates,
        request.existing_dates,
        start=request.start,
        end=request.end,
        refresh=request.refresh,
    )
    if isinstance(plan_result, Failure):
        return Failure(IngestionPreflightError(range_error=plan_result.error))

    compliance_denial = _compliance_denial(request.compliance_profile)
    missing_credential = [
        provider for provider, present in request.credentials.items() if not present
    ]
    preflight_result = storage_preflight(
        request.storage_estimate,
        request.storage_available,
        plan_result.value.requested_dates,
    )

    if compliance_denial is not None:
        return Failure(IngestionPreflightError(compliance_denial=compliance_denial))
    if missing_credential:
        return Failure(
            IngestionPreflightError(credential_denial=",".join(sorted(missing_credential)))
        )
    if isinstance(preflight_result, Failure):
        return Failure(IngestionPreflightError(storage_error=preflight_result.error))

    return Success(
        IngestionPreflight(
            plan=plan_result.value,
            allowed_provider_dates=plan_result.value.requested_dates,
        )
    )
