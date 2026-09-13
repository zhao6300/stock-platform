from __future__ import annotations

from datetime import date
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.common import Failure, Success
from stock_platform.domain.ingestion import (
    FundNavCandidate,
    normalize_fund_nav,
)


def fund_nav_issues(candidate: FundNavCandidate) -> tuple[str, ...]:
    """Return every canonical fund NAV field that would reject the row."""
    issues: list[str] = []
    if candidate.unit_nav <= 0:
        issues.append("unit_nav")
    if candidate.cumulative_nav is not None and candidate.cumulative_nav <= 0:
        issues.append("cumulative_nav")
    if (
        candidate.cumulative_nav is not None
        and candidate.cumulative_nav < candidate.unit_nav
    ):
        issues.append("cumulative_nav")
    return tuple(issues)


@given(
    candidate=st.builds(
        FundNavCandidate,
        observation_date=st.just(date(2026, 1, 2)),
        unit_nav=st.decimals(
            allow_nan=False, allow_infinity=False, min_value=Decimal("0.01")
        ),
        cumulative_nav=st.decimals(
            allow_nan=False,
            allow_infinity=False,
            min_value=Decimal("0.01"),
            max_value=Decimal("1e10"),
        ),
        currency=st.just("CNY"),
    ),
)
def test_fund_nav_acceptance_is_canonical(
    candidate: FundNavCandidate,
) -> None:
    """Fund NAV acceptance is equivalent to all canonical constraints."""
    result = normalize_fund_nav(candidate, "CNY")
    issues = fund_nav_issues(candidate)
    if issues:
        assert isinstance(result, Failure)
        assert result.error.fields == frozenset(issues)
    else:
        assert isinstance(result, Success)
