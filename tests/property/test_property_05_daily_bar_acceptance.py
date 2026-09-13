from __future__ import annotations

from datetime import date
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.common import Failure
from stock_platform.domain.ingestion import (
    DailyBarCandidate,
    normalize_daily_bar,
)


def daily_bar_issues(candidate: DailyBarCandidate) -> frozenset[str]:
    """Return every canonical daily bar field that would reject the row."""
    issues: list[str] = []
    if candidate.open <= 0:
        issues.append("open")
    if candidate.high < max(candidate.open, candidate.low, candidate.close):
        issues.append("high")
    if candidate.low > min(candidate.open, candidate.close, candidate.high):
        issues.append("low")
    if candidate.close <= 0:
        issues.append("close")
    if candidate.volume < 0:
        issues.append("volume")
    if candidate.turnover < 0:
        issues.append("turnover")
    return frozenset(issues)


@given(
    candidate=st.builds(
        DailyBarCandidate,
        observation_date=st.just(date(2026, 1, 2)),
        open=st.decimals(
            allow_nan=False, allow_infinity=False, min_value=Decimal("0.01")
        ),
        high=st.decimals(
            allow_nan=False, allow_infinity=False, min_value=Decimal("0.01")
        ),
        low=st.decimals(
            allow_nan=False, allow_infinity=False, min_value=Decimal("0.01")
        ),
        close=st.decimals(
            allow_nan=False, allow_infinity=False, min_value=Decimal("0.01")
        ),
        volume=st.decimals(
            allow_nan=False, allow_infinity=False, min_value=Decimal("0")
        ),
        turnover=st.decimals(
            allow_nan=False, allow_infinity=False, min_value=Decimal("0")
        ),
        currency=st.just("CNY"),
    ),
)
def test_daily_bar_acceptance_is_canonical(
    candidate: DailyBarCandidate,
) -> None:
    """Daily Bar acceptance is equivalent to all canonical constraints."""
    result = normalize_daily_bar(candidate, "CNY")
    issues = daily_bar_issues(candidate)
    if issues:
        assert isinstance(result, Failure)
