from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from stock_platform.domain.common import Failure, Success
from stock_platform.domain.compliance import (
    AccountType,
    ComplianceProfileVersion,
    ComplianceValidator,
)

_FOUR_PURPOSES = (
    "PERSONAL_RESEARCH",
    "ACADEMIC_RESEARCH",
    "COMMERCIAL_RESEARCH",
    "REDISTRIBUTION",
)
_FOUR_PURPOSES_NAME = _FOUR_PURPOSES[0]


def _profile() -> ComplianceProfileVersion:
    return ComplianceProfileVersion(
        profile_id="profile",
        provider_name="provider",
        data_source="source",
        account_type=AccountType.FREE,
        permitted_purposes=("PERSONAL_RESEARCH",),
        retention_permission="PROHIBITED",
        export_permission="DERIVED_RESULTS_ONLY",
        confirmation_time=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
    )


def test_compliance_validation_is_conjunctive_and_reports_all_violations() -> None:
    invalid = replace(
        _profile(),
        provider_name="",
        data_source="",
        permitted_purposes=(),
        retention_permission="NOT_A_RETENTION_PERMISSION",
        export_permission="NOT_AN_EXPORT_PERMISSION",
        confirmation_time=datetime(2026, 1, 2, 3, 4, 5, 6, tzinfo=UTC),
    )

    valid = ComplianceValidator.validate(_profile())
    failed = ComplianceValidator.validate(invalid)

    assert isinstance(valid, Success)
    assert isinstance(failed, Failure)
    assert failed.error.fields == frozenset(
        {
            "provider_name",
            "data_source",
            "permitted_purposes",
            "retention_permission",
            "export_permission",
            "confirmation_time",
        }
    )
