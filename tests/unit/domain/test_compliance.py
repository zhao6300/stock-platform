from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

from stock_platform.domain.common import Failure, Success
from stock_platform.domain.compliance import (
    AccountType,
    ComplianceProfileVersion,
    ComplianceValidator,
)


def _profile() -> ComplianceProfileVersion:
    return ComplianceProfileVersion(
        profile_id="test-profile",
        provider_name="provider",
        data_source="api",
        account_type=AccountType.FREE,
        permitted_purposes=("PERSONAL_RESEARCH",),
        retention_permission="PROHIBITED",
        export_permission="DERIVED_RESULTS_ONLY",
        confirmation_time=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
    )


def test_active_profile_is_valid() -> None:
    result = ComplianceValidator.validate(_profile())

    assert isinstance(result, Success)


def test_empty_profile_provider_name_is_rejected() -> None:
    result = ComplianceValidator.validate(dataclasses.replace(_profile(), provider_name=""))

    assert isinstance(result, Failure)
