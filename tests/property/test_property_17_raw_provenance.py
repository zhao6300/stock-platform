from __future__ import annotations

from datetime import UTC, datetime

from stock_platform.domain.compliance import (
    AccountType,
    ComplianceProfileVersion,
    RetainedRawResponse,
)


def _profile() -> ComplianceProfileVersion:
    return ComplianceProfileVersion(
        profile_id="profile",
        provider_name="provider",
        data_source="source",
        account_type=AccountType.FREE,
        permitted_purposes=("PERSONAL_RESEARCH",),
        retention_permission="RAW_AND_NORMALIZED_PROVIDER_DATA",
        export_permission="RAW_PROVIDER_DATA",
        confirmation_time=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
    )


def test_retained_raw_data_has_complete_provenance() -> None:
    profile = _profile()
    response = RetainedRawResponse(
        provider=profile.provider_name,
        request_parameters={"date": "2026-01-02"},
        profile=profile,
        request_time=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
    )

    assert response.provider == "provider"
    assert response.request_parameters == {"date": "2026-01-02"}
    assert response.profile is profile
    assert response.request_time.microsecond == 0
