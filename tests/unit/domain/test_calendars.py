from __future__ import annotations

from datetime import UTC, date, datetime

from stock_platform.domain.calendars import (
    CalendarResolutionError,
    CalendarService,
    CalendarVersion,
)
from stock_platform.domain.common import Failure, Success


def _versions() -> CalendarService:
    return CalendarService(
        [
            CalendarVersion(
                version_id="2026-h1",
                market="CN",
                timezone="Asia/Shanghai",
                valid_from=date(2026, 1, 1),
                valid_to=date(2026, 6, 30),
                kind="TRADING",
                open_dates=frozenset([date(2026, 1, 2), date(2026, 6, 30)]),
                expected_dates=None,
            ),
            CalendarVersion(
                version_id="2026-h2",
                market="CN",
                timezone="Asia/Shanghai",
                valid_from=date(2026, 7, 1),
                valid_to=date(2026, 12, 31),
                kind="TRADING",
                open_dates=frozenset([date(2026, 7, 1)]),
                expected_dates=None,
            ),
        ]
    )


def test_trading_observation_is_unique_in_market_time_zone() -> None:
    versions = _versions()

    resolved = versions.observation_date(datetime(2026, 1, 1, 23, 59, tzinfo=UTC), kind="TRADING")

    assert resolved == Success(date(2026, 1, 2))
    assert versions.is_open("CN", date(2026, 6, 30)) is True
    assert versions.open_dates("CN") == (
        date(2026, 1, 2),
        date(2026, 6, 30),
        date(2026, 7, 1),
    )


def test_missing_applicable_version_is_rejected() -> None:
    versions = _versions()

    assert versions.observation_date(datetime(2027, 1, 1, tzinfo=UTC), kind="TRADING") == Failure(
        CalendarResolutionError("missing")
    )
