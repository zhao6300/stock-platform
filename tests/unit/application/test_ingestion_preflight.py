from __future__ import annotations

from datetime import UTC, date, datetime

from stock_platform.application.ingestion_preflight import (
    IngestionPreflightRequest,
    ingestion_preflight,
)
from stock_platform.domain.common import Failure, Success
from stock_platform.domain.compliance import (
    AccountType,
    ComplianceProfileVersion,
)


def _valid_profile(
    retention_permission: str = "NORMALIZED_PROVIDER_DATA",
    export_permission: str = "NORMALIZED_PROVIDER_DATA",
) -> ComplianceProfileVersion:
    return ComplianceProfileVersion(
        profile_id="profile-1",
        provider_name="alpha",
        data_source="provider",
        account_type=AccountType.PAID_PERSONAL,
        permitted_purposes=("PERSONAL_RESEARCH",),
        retention_permission=retention_permission,
        export_permission=export_permission,
        confirmation_time=datetime(2026, 1, 31, tzinfo=UTC),
    )


def test_ingestion_preflight_passes_all_local_gates() -> None:
    result = ingestion_preflight(
        IngestionPreflightRequest(
            expected_dates=(date(2026, 1, 2), date(2026, 1, 3)),
            existing_dates=(date(2026, 1, 2),),
            start=date(2026, 1, 2),
            end=date(2026, 1, 3),
            refresh=False,
            compliance_profile=_valid_profile(),
            credentials={"alpha": True},
            storage_estimate=10,
            storage_available=20,
        )
    )

    assert isinstance(result, Success)
    assert result.value.plan.requested_dates == (date(2026, 1, 3),)
    assert result.value.allowed_provider_dates == (date(2026, 1, 3),)


def test_ingestion_preflight_reports_invalid_range_and_blocks_network() -> None:
    result = ingestion_preflight(
        IngestionPreflightRequest(
            expected_dates=(),
            existing_dates=(),
            start=date(2026, 1, 3),
            end=date(2026, 1, 2),
            refresh=False,
            compliance_profile=_valid_profile(),
            credentials={"alpha": True},
            storage_estimate=0,
            storage_available=0,
        )
    )

    assert isinstance(result, Failure)
    assert result.error.range_error is not None
    assert result.error.compliance_denial is None
    assert result.error.storage_error is None


def test_ingestion_preflight_rejects_prohibited_compliance_and_absent_credentials() -> None:
    no_retention = ingestion_preflight(
        IngestionPreflightRequest(
            expected_dates=(date(2026, 1, 2),),
            existing_dates=(),
            start=date(2026, 1, 2),
            end=date(2026, 1, 2),
            refresh=False,
            compliance_profile=_valid_profile(retention_permission="PROHIBITED"),
            credentials={"alpha": True},
            storage_estimate=0,
            storage_available=0,
        )
    )
    absent_credential = ingestion_preflight(
        IngestionPreflightRequest(
            expected_dates=(date(2026, 1, 2),),
            existing_dates=(),
            start=date(2026, 1, 2),
            end=date(2026, 1, 2),
            refresh=False,
            compliance_profile=_valid_profile(),
            credentials={"alpha": False},
            storage_estimate=0,
            storage_available=0,
        )
    )

    assert isinstance(no_retention, Failure)
    assert no_retention.error.compliance_denial == "retention_permission"
    assert isinstance(absent_credential, Failure)
    assert absent_credential.error.credential_denial == "alpha"
