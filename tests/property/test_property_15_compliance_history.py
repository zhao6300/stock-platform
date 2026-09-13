from __future__ import annotations

from datetime import UTC, datetime

from stock_platform.domain.compliance import (
    AccountType,
    ComplianceHistory,
    ComplianceProfileVersion,
)

_LEGALLY_PERMITTED_MINUTES = 0
_MINUTES_IN_HOUR = 60
_SECOND_PRECISION_MICROSECONDS = 0


def _profile(confirmation_time: datetime) -> ComplianceProfileVersion:
    return ComplianceProfileVersion(
        profile_id="profile",
        provider_name="operator",
        data_source="source",
        account_type=AccountType.FREE,
        permitted_purposes=("PERSONAL_RESEARCH", "ACADEMIC_RESEARCH"),
        retention_permission="NORMALIZED_PROVIDER_DATA",
        export_permission="DERIVED_RESULTS_ONLY",
        confirmation_time=confirmation_time,
    )


def test_compliance_history_is_append_only() -> None:
    history = ComplianceHistory()
    assert not history.profile_history()
    first = history.append(_profile(datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)))
    assert first.version == history.profile_history()[0].version
