from __future__ import annotations

from datetime import date

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.calendars import CalendarService, CalendarVersion


def _version(kind: str, valid_from: date, valid_to: date, market: str, timezone: str) -> CalendarVersion:
    open_dates = frozenset([valid_from]) if kind == "TRADING" else None
    expected_dates = frozenset([valid_from]) if kind == "VALUATION" else None
    return CalendarVersion(
        version_id=f"{market}-{kind}-{valid_from}",
        market=market,
        timezone=timezone,
        valid_from=valid_from,
        valid_to=max(valid_from, valid_to),
        kind=kind,
        open_dates=open_dates,
        expected_dates=expected_dates,
    )


@given(
    versions=st.lists(
        st.builds(
            _version,
            market=st.sampled_from(("CN", "HK", "FUND")),
            timezone=st.sampled_from(("UTC", "Asia/Shanghai", "Hongkong")),
                valid_from=st.dates(min_value=date(2020, 1, 1), max_value=date(2026, 12, 31)),
                valid_to=st.dates(
                    min_value=date(2020, 1, 2),
                    max_value=date(2027, 12, 31),
                ),
            kind=st.sampled_from(("TRADING", "VALUATION")),
        )
    )
)
def test_version_sets_are_consistent(versions: list[CalendarVersion]) -> None:
    try:
        service = CalendarService(tuple(versions))
    except ValueError:
        return
    for version in versions:
        if version.kind == "TRADING":
            assert service.is_open(version.market, next(iter(version.open_dates or ())))
        else:
            assert service.is_expected(version.market, next(iter(version.expected_dates or ())))
