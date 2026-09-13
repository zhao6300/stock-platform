from __future__ import annotations

from datetime import date
from decimal import Decimal

from stock_platform.domain.common import Failure, Success
from stock_platform.domain.ingestion import (
    DailyBarCandidate,
    DailyBarValidationError,
    FundNavCandidate,
    ObservationRunOutcome,
    ObservationVersion,
    decide_observation_version,
    normalize_daily_bar,
    normalize_fund_nav,
    observation_run_counts,
    planned_ingestion_dates,
)


def test_planned_ingestion_dates_selects_missing_segments() -> None:
    expected = (
        date(2026, 1, 2),
        date(2026, 1, 3),
        date(2026, 1, 5),
        date(2026, 1, 6),
        date(2026, 1, 7),
    )
    existing = frozenset((date(2026, 1, 3), date(2026, 1, 7)))

    result = planned_ingestion_dates(
        expected,
        existing_dates=sorted(existing),
        start=date(2026, 1, 2),
        end=date(2026, 1, 7),
    )

    assert isinstance(result, Success)
    assert result.value.version_id
    assert result.value.requested_dates == (
        date(2026, 1, 2),
        date(2026, 1, 5),
        date(2026, 1, 6),
    )


def test_refresh_planning_ignores_existing_dates() -> None:
    expected = (date(2026, 1, 2), date(2026, 1, 3))
    existing = (date(2026, 1, 2), date(2026, 1, 3))

    result = planned_ingestion_dates(
        expected,
        existing_dates=existing,
        start=date(2026, 1, 2),
        end=date(2026, 1, 3),
        refresh=True,
    )

    assert isinstance(result, Success)
    assert result.value.version_id
    assert result.value.requested_dates == expected


def test_invalid_ingestion_range_fails_before_planning() -> None:
    result = planned_ingestion_dates(
        (),
        existing_dates=(),
        start=date(2026, 1, 3),
        end=date(2026, 1, 2),
    )

    assert isinstance(result, Failure)


def _valid_daily_bar() -> DailyBarCandidate:
    return DailyBarCandidate(
        observation_date=date(2026, 1, 2),
        open=Decimal("10.0"),
        high=Decimal("11.0"),
        low=Decimal("9.0"),
        close=Decimal("10.5"),
        volume=Decimal("1000"),
        turnover=Decimal("10000.0"),
        currency="CNY",
    )


def test_valid_daily_bar_normalizes_completely() -> None:
    result = normalize_daily_bar(_valid_daily_bar(), "CNY")

    assert isinstance(result, Success)
    assert result.value.close == Decimal("10.5")


def test_inverted_daily_bar_rejects_every_field() -> None:
    candidate = DailyBarCandidate(
        observation_date=date(2026, 1, 2),
        open=Decimal("100.0"),
        high=Decimal("11.0"),
        low=Decimal("9.0"),
        close=Decimal("10.5"),
        volume=Decimal("1000"),
        turnover=Decimal("10000.0"),
        currency="CNY",
    )

    assert normalize_daily_bar(candidate, "CNY") == Failure(
        DailyBarValidationError(frozenset(("open", "high", "low", "close", "volume", "turnover")))
    )


def test_valid_fund_nav_normalizes_completely() -> None:
    candidate = FundNavCandidate(
        observation_date=date(2026, 1, 2),
        unit_nav=Decimal("1.20"),
        cumulative_nav=Decimal("1.30"),
        currency="CNY",
    )

    result = normalize_fund_nav(candidate, "CNY")

    assert isinstance(result, Success)
    assert result.value.unit_nav == Decimal("1.20")
    assert result.value.cumulative_nav == Decimal("1.30")


def test_non_positive_fund_nav_rejects_the_entire_row() -> None:
    candidate = FundNavCandidate(observation_date=date(2026, 1, 2), unit_nav=Decimal("0"))

    result = normalize_fund_nav(candidate, "CNY")
    assert isinstance(result, Failure)


def test_fund_nav_error_reports_cumulative_mismatch() -> None:
    candidate = FundNavCandidate(
        observation_date=date(2026, 1, 2),
        unit_nav=Decimal("1.0"),
        cumulative_nav=Decimal("0.5"),
        currency="CNY",
    )

    result = normalize_fund_nav(candidate, "CNY")
    assert isinstance(result, Failure)


def _observation_version(field_values: tuple[str, str]) -> ObservationVersion:
    return ObservationVersion(
        version_id="a-version",
        security_id="security-a",
        data_type="DAILY_BAR",
        observation_date=date(2026, 1, 2),
        field_values=frozenset((field_values,)),
    )


def test_equal_observation_reuses_current_version() -> None:
    current = _observation_version(("close", "10.5"))
    incoming = _observation_version(("close", "10.5"))

    decision = decide_observation_version(current, incoming)

    assert decision.version_is_new is False
    assert decision.version_id == current.version_id
    assert decision.predecessor_id == current.predecessor_id


def test_changed_observation_adds_a_child_version() -> None:
    current = _observation_version(("close", "10.5"))
    changed = ObservationVersion(
        version_id="b-version",
        security_id="security-a",
        data_type="DAILY_BAR",
        observation_date=date(2026, 1, 2),
        field_values=frozenset((("close", "10.6"),)),
    )

    decision = decide_observation_version(current, changed)

    assert decision.version_is_new is True
    assert decision.version_id == changed.version_id
    assert decision.predecessor_id == current.version_id


def test_observation_run_counts_conserves_and_excludes_categories() -> None:
    counts = observation_run_counts(
        requested=4,
        outcomes=(
            ObservationRunOutcome(True, False, False, False),
            ObservationRunOutcome(False, False, True, False),
            ObservationRunOutcome(False, False, True, False),
            ObservationRunOutcome(False, False, False, True),
        ),
    )

    assert isinstance(counts, Success)
    assert counts.value.accepted == 1
    assert counts.value.warning == 0
    assert counts.value.rejected == len(
        (
            "rejected-1",
            "rejected-2",
        )
    )
    assert counts.value.unresolved == 1
    assert (
        counts.value.accepted
        + counts.value.warning
        + counts.value.rejected
        + counts.value.unresolved
        == counts.value.requested
    )
