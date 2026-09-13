from __future__ import annotations

from datetime import UTC, datetime

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.application.exports import (
    ExportAuthorization,
    ExportDenied,
    authorize_export,
)
from stock_platform.domain.compliance import AccountType, ComplianceProfileVersion


def _profile(export_permission: str) -> ComplianceProfileVersion:
    return ComplianceProfileVersion(
        profile_id="profile",
        provider_name="provider",
        data_source="source",
        account_type=AccountType.FREE,
        permitted_purposes=("PERSONAL_RESEARCH",),
        retention_permission="PROHIBITED",
        export_permission=export_permission,  # type: ignore[arg-type]
    confirmation_time=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
    )


@given(
    export_permission=st.sampled_from(
        ("PROHIBITED", "DERIVED_RESULTS_ONLY", "NORMALIZED_PROVIDER_DATA", "RAW_PROVIDER_DATA")
    ),
    category=st.sampled_from(("RAW_PROVIDER_DATA", "NORMALIZED_PROVIDER_DATA", "DERIVED_RESULTS")),
)
def test_export_authorization_is_category_and_profile_bound(
    export_permission: str,
    category: str,
) -> None:
    profile = _profile(export_permission)
    result = authorize_export(profile, category)  # type: ignore[arg-type]

    if isinstance(result, ExportDenied):
        assert result.profile is profile
        assert result.category == category
        return
    assert isinstance(result, ExportAuthorization)
    assert result.profile is profile
    assert result.category == category
    assert result.payload_bytes == b""
