from __future__ import annotations

from datetime import date, datetime

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.application.ingestion_preflight import (
    IngestionPreflightRequest,
    ingestion_preflight,
)
from stock_platform.domain.common import Failure, Success
from stock_platform.domain.compliance import AccountType, ComplianceProfileVersion

profile = ComplianceProfileVersion(
    profile_id="profile-1",
    provider_name="alpha",
    data_source="provider",
    account_type=AccountType.PAID_PERSONAL,
    permitted_purposes=("PERSONAL_RESEARCH",),
    retention_permission="NORMALIZED_PROVIDER_DATA",
    export_permission="NORMALIZED_PROVIDER_DATA",
    confirmation_time=datetime(2026, 1, 31),
)


@given(
    storage_estimate=st.integers(min_value=0, max_value=1 << 40),
    storage_available=st.integers(min_value=0, max_value=1 << 40),
)
def test_storage_preflight_is_exact(storage_estimate: int, storage_available: int) -> None:
    result = ingestion_preflight(
        IngestionPreflightRequest(
            expected_dates=(date(2026, 1, 2),),
            existing_dates=(),
            start=date(2026, 1, 2),
            end=date(2026, 1, 2),
            refresh=False,
            compliance_profile=profile,
            credentials={"alpha": True},
            storage_estimate=storage_estimate,
            storage_available=storage_available,
        )
    )

    if storage_available >= storage_estimate:
        assert isinstance(result, Success)
        assert result.value.allowed_provider_dates == (date(2026, 1, 2),)
    else:
        assert isinstance(result, Failure)
        assert result.error.storage_error is not None
        assert result.error.storage_error.estimated_bytes == storage_estimate
        assert result.error.storage_error.available_bytes == storage_available
