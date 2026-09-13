from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from hypothesis import strategies as st


def uids() -> st.SearchStrategy[int]:
    """Generate safe test identifiers for a local platform owner and caller."""
    return st.integers(min_value=1000, max_value=1_000_000_000)


def dates(*, min_value: int = 1900, max_value: int = 2999) -> st.SearchStrategy[date]:
    """Generate valid ISO calendar dates."""
    return st.dates(
        min_value=date(min_value, 1, 1),
        max_value=date(max_value, 12, 31),
    )


def utc_datetimes() -> st.SearchStrategy[datetime]:
    """Generate timezone-aware UTC timestamps with bounded test size."""
    return st.datetimes(
        min_value=datetime(1900, 1, 1, tzinfo=UTC),
        max_value=datetime(2999, 12, 31, tzinfo=UTC),
    ).map(lambda value: value.astimezone(UTC))


def decimals() -> st.SearchStrategy[Decimal]:
    """Generate finite decimal values suitable for money and factor tests."""
    return st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("1e18"),
        places=10,
        allow_nan=False,
        allow_infinity=False,
    )


def durations(
    *,
    min_seconds: int = 0,
    max_seconds: int = 365 * 24 * 60 * 60,
) -> st.SearchStrategy[timedelta]:
    """Generate ordered durations for calendar and retry tests."""
    return st.timedeltas(min_value=timedelta(seconds=min_seconds), max_value=timedelta(seconds=max_seconds))
