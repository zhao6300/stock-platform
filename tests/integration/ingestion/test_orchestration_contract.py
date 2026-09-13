from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest

from stock_platform.application.ingestion import (
    IngestionOperation,
    IngestionStatus,
    MissingFieldError,
    ProviderFailure,
    PublicationFailure,
    run_ingestion,
)
from stock_platform.domain.common import Failure, Result, Success
from stock_platform.domain.ingestion import DailyBar, ObservationVersion
from stock_platform.domain.quality import QualityReport


@dataclass
class FakePorts:
    available: int
    provisional_dates: list[date] | None = None
    published_dates: list[date] | None = None
    prior_run_id: str | None = None
    test_run_id: str | None = None
    normalized: list[Result[DailyBar, MissingFieldError]] | None = None
    quality: QualityReport | None = None
    fetched: list[date] = None  # type: ignore
    current: ObservationVersion | None = None
    candidate: ObservationVersion | None = None
    daily_bar: DailyBar | None = None
    normalize_failure: bool = False
    publish_fails: bool = False

    def provider_fetch(self, request: Any, observation_date: date):
        self.fetched.append(observation_date)
        if observation_date == date(2026, 1, 2):
            return Failure(ProviderFailure("fake-provider", "RATE_LIMIT", (observation_date,)))
        return Success(self.daily_bar)

    def normalize(self, envelope: Any):
        if self.normalize_failure:
            return Failure(MissingFieldError({"close"}))
        return Success(self.daily_bar)

    def quality_assess(self, observation: DailyBar) -> QualityReport:
        return self.quality

    def current_version(self, observation: DailyBar) -> ObservationVersion | None:
        return self.current

    def candidate_version(self, observation: DailyBar) -> ObservationVersion:
        return self.candidate

    def publish(self, current, candidate, report):
        if self.publish_fails and candidate.observation_date == date(2026, 1, 2):
            return Failure(PublicationFailure(candidate.observation_date, "publish-down"))
        return Success(candidate)


def _daily_date(value: int) -> DailyBar:
    return DailyBar(
        observation_date=date(2026, 1, value),
        open=Decimal("10"),
        high=Decimal("11"),
        low=Decimal("9"),
        close=Decimal("10"),
        volume=Decimal("1000"),
        turnover=Decimal("100000"),
        currency="USD",
    )


def _operation(frozenset_dates: frozenset[date] | None = None) -> IngestionOperation:
    return IngestionOperation(
        request_id="ingest-1",
        dates=(date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)),
        storage_estimate=1,
        storage_available=1,
        finalized_before=frozenset(frozenset_dates or set()),
        provider_request={"provider": "fake-provider"},
        start=date(2026, 1, 1),
        end=date(2026, 1, 3),
    )


def _quality() -> QualityReport:
    return QualityReport(
        scope="ingest-1",
        rule_version_id="quality-v1",
        issues=(),
        generated_at=datetime(2026, 1, 2, tzinfo=UTC),
    )


@pytest.fixture
def latest_observation():
    return ObservationVersion(
        version_id="stored-v1",
        security_id="security-1",
        data_type="DailyBar",
        observation_date=date(2026, 1, 1),
        field_values=frozenset({("close", "10")}),
    )


@pytest.fixture
def next_observation(latest_observation):
    return ObservationVersion(
        version_id="incoming-v2",
        security_id=latest_observation.security_id,
        data_type=latest_observation.data_type,
        observation_date=date(2026, 1, 2),
        field_values=latest_observation.field_values,
    )


@pytest.fixture
def daily_bar() -> DailyBar:
    return _daily_date(1)


@pytest.fixture
def daily_quality() -> QualityReport:
    return QualityReport(
        scope="ingest-1",
        rule_version_id="quality-v1",
        issues=(),
        generated_at=datetime(2026, 1, 2, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_provider_failure_after_first_date(
    latest_observation,
    next_observation,
    daily_bar,
    daily_quality,
) -> None:
    ports = FakePorts(
        available=1,
        current=latest_observation,
        candidate=next_observation,
        daily_bar=daily_bar,
        quality=daily_quality,
        fetched=[],
        provisional_dates=[date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)],
        published_dates=[date(2026, 1, 1), date(2026, 1, 3)],
    )
    result = await run_ingestion(_operation(), ports)
    assert isinstance(result, Failure)
    assert result.error.provider_failures[0].category == "RATE_LIMIT"
    assert result.error.value.finalized_dates == {date(2026, 1, 1)}
    assert result.error.value.resumable_boundary == date(2026, 1, 2)


@pytest.mark.asyncio
async def test_missing_fields_are_rejected(
    latest_observation,
    next_observation,
    daily_bar,
    daily_quality,
) -> None:
    ports = FakePorts(
        available=1,
        current=latest_observation,
        candidate=next_observation,
        daily_bar=daily_bar,
        quality=daily_quality,
        fetched=[],
        provisional_dates=[date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)],
        published_dates=[date(2026, 1, 1), date(2026, 1, 3)],
        normalize_failure=True,
    )
    result = await run_ingestion(_operation(frozenset({date(2026, 1, 3)})), ports)
    assert isinstance(result, Failure)
    assert result.error.value.status is IngestionStatus.INCOMPLETE
    assert result.error.value.finalized_dates == {date(2026, 1, 1), date(2026, 1, 3)}


@pytest.mark.asyncio
async def test_publication_failure_preserves_other_dates(
    latest_observation,
    next_observation,
    daily_bar,
    daily_quality,
) -> None:
    ports = FakePorts(
        available=1,
        current=latest_observation,
        candidate=next_observation,
        daily_bar=daily_bar,
        quality=daily_quality,
        fetched=[],
        provisional_dates=[date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)],
        published_dates=[date(2026, 1, 1), date(2026, 1, 3)],
        publish_fails=True,
    )
    result = await run_ingestion(_operation(frozenset({date(2026, 1, 3)})), ports)
    assert isinstance(result, Failure)
    assert result.error.value.finalized_dates == {date(2026, 1, 1), date(2026, 1, 3)}
    assert result.error.value.resumable_boundary == date(2026, 1, 2)


@pytest.mark.asyncio
async def test_storage_preflight_blocks_every_fetch() -> None:
    ports = FakePorts(available=0, daily_bar=None, quality=_quality(), fetched=[])
    result = await run_ingestion(
        IngestionOperation(
            request_id="ingest-1",
            dates=(date(2026, 1, 1),),
            storage_estimate=1,
            storage_available=0,
            visible_dates=frozenset({date(2026, 1, 1)}),
        ),
        ports,
    )
    assert isinstance(result, Failure)
    assert ports.fetched == []
    assert ports.available == 0
