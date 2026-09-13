from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.calendars import CalendarService, CalendarVersion
from stock_platform.domain.common import Success


def _version(
    market: str,
    timezone: str,
    valid_from: date,
    valid_to: date,
    kind: str,
) -> CalendarVersion:
    open_dates = frozenset([valid_from]) if kind == "TRADING" else None
    expected_dates = frozenset([valid_from]) if kind == "VALUATION" else None
    return CalendarVersion(
        version_id=f"{market}-{kind}-{valid_from}",
        market=market,
        timezone=timezone,
        valid_from=valid_from,
        valid_to=valid_to,
        kind=kind,
        open_dates=open_dates,
        expected_dates=expected_dates,
    )


@given(
    timestamp=st.datetimes(
        min_value=datetime(1990, 1, 1),
        max_value=datetime(2999, 12, 31),
        allow_imaginary=False,
    ).map(lambda value: value.replace(tzinfo=UTC))
)
def test_unique_timezones_convert_timestamps_to_the_same_local_date(
    timestamp: datetime,
) -> None:
    local_date = timestamp.astimezone(ZoneInfo("Asia/Shanghai")).date()
    version = CalendarVersion(
        version_id="CN-OPEN",
        market="CN",
        timezone="Asia/Shanghai",
        valid_from=date(1900, 1, 1),
        valid_to=date(3000, 12, 31),
        kind="TRADING",
        open_dates=frozenset([local_date]),
        expected_dates=None,
    )
    service = CalendarService((version,))

    result = service.observation_date(timestamp, kind="TRADING")

    local_date = timestamp.astimezone(ZoneInfo("Asia/Shanghai")).date()
    assert result == Success(local_date)
    assert service.is_open("CN", local_date)
