from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from stock_platform.application.ingestion import (
    IngestionOperation,
    run_ingestion,
)
from stock_platform.application.ingestion_preflight import (
    IngestionPreflightRequest,
    ingestion_preflight,
)
from stock_platform.domain.common import Failure, Success
from stock_platform.domain.compliance import (
    AccountType,
    ComplianceProfileVersion,
)
from stock_platform.domain.ingestion import DailyBar, ObservationVersion
from stock_platform.domain.quality import QualityReport


@dataclass
class ResumePorts:
    quality: QualityReport
    daily: DailyBar
    observation: ObservationVersion
    fetched: list[date]

    def provider_fetch(self, _request, _observation_date):
        self.fetched.append(_observation_date)
        return Success(self.daily)

    def normalize(self, envelope):
        return Success(self.daily)

    def quality_assess(self, observation):
        return self.quality

    def current_version(self, observation):
        return self.observation

    def candidate_version(self, observation):
        return self.observation

    def publish(self, current, candidate, report):
        return Success(candidate)


def _quality() -> QualityReport:
    return QualityReport(
        scope="ingest-resume-1",
        rule_version_id="quality-v1",
        issues=(),
        generated_at=datetime(2026, 1, 2, tzinfo=UTC),
    )


def _daily_bar(observation_date: int) -> DailyBar:
    return DailyBar(
        observation_date=date(2026, 1, observation_date),
        open=Decimal("10"),
        high=Decimal("11"),
        low=Decimal("9"),
        close=Decimal("10"),
        volume=Decimal("1000"),
        turnover=Decimal("10000"),
        currency="USD",
    )


@pytest.mark.asyncio
async def test_resume_requests_the_unfinalized_complement() -> None:
    quality = _quality()
    observation = ObservationVersion(
        version_id="stored-v1",
        security_id="security-1",
        data_type="DailyBar",
        observation_date=date(2026, 1, 1),
        field_values=frozenset({("close", "10")}),
    )
    ports = ResumePorts(
        quality=quality,
        daily=_daily_bar(1),
        observation=observation,
        fetched=[],
    )
    operation = IngestionOperation(
        request_id="ingest-resume-1",
        dates=(date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)),
        storage_estimate=10,
        storage_available=10,
        finalized_before=frozenset({date(2026, 1, 2)}),
        provider_request={"provider": "fake-provider"},
        start=date(2026, 1, 1),
        end=date(2026, 1, 3),
    )

    result = await run_ingestion(operation, ports)

    assert ports.fetched == [date(2026, 1, 1), date(2026, 1, 3)]
    assert isinstance(result, Success)
    assert result.value.finalized_dates == frozenset(
        (date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3))
    )


def test_compliance_gate_blocks_ingestion_before_any_network_call() -> None:
    profile = ComplianceProfileVersion(
        profile_id="profile-1",
        provider_name="alpha",
        data_source="provider",
        account_type=AccountType.PAID_PERSONAL,
        permitted_purposes=("PERSONAL_RESEARCH",),
        retention_permission="PROHIBITED",
        export_permission="NORMALIZED_PROVIDER_DATA",
        confirmation_time=datetime(2026, 1, 31, tzinfo=UTC),
    )
    result = ingestion_preflight(
        IngestionPreflightRequest(
            expected_dates=(date(2026, 1, 1), date(2026, 1, 2)),
            existing_dates=(),
            start=date(2026, 1, 1),
            end=date(2026, 1, 2),
            refresh=False,
            compliance_profile=profile,
            credentials={"alpha": True},
            storage_estimate=1,
            storage_available=10,
        )
    )

    assert isinstance(result, Failure)
    assert result.error.compliance_denial == "retention_permission"
