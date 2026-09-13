from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Literal
from zoneinfo import ZoneInfo

from stock_platform.domain.common import Failure, Result, Success
from stock_platform.domain.observation import Observation

type CalendarKind = str


class ObservationGapReason(StrEnum):
    """The single precedence-defined classification of an absent observation."""

    CLOSED_DATE_EXPECTED_GAP = "CLOSED_DATE_EXPECTED_GAP"
    SUSPENDED_ON_OPEN_DATE = "SUSPENDED_ON_OPEN_DATE"
    MISSING_SECURITY_MASTER = "MISSING_SECURITY_MASTER"
    MISSING_VALUATION_DATE = "MISSING_VALUATION_DATE"
    MISSING_OR_UNKNOWN_TRADABILITY = "MISSING_OR_UNKNOWN_TRADABILITY"
    EXPECTED_VALUATION_DELAYED_OR_MISSING = "EXPECTED_VALUATION_DELAYED_OR_MISSING"


class ObservationGapReasonDetailed(StrEnum):
    """The detailed reason to attach when an observation is missing."""

    MISSING_SECURITY_MASTER = "MISSING_SECURITY_MASTER"
    MISSING_TRADING_DATE = "MISSING_TRADING_DATE"
    MISSING_VALUATION_DATE = "MISSING_VALUATION_DATE"
    NOT_CONNECTED = "NOT_CONNECTED"


class ObservationGapClassification(StrEnum):
    """The one precedence-defined reason used for reporting a missing date."""

    EXPECTED_CALENDAR_GAP = "EXPECTED_CALENDAR_GAP"
    SUSPENDED_TRADING_GAP = "SUSPENDED_TRADING_GAP"
    UNRESOLVED_GAP = "UNRESOLVED_GAP"
    DELAYED_OR_MISSING_VALUATION = "DELAYED_OR_MISSING_VALUATION"


def classify_observation_gap(
    trading_calendar_open: bool,
    tradability_status: str | None,
    valuation_expected: bool,
) -> ObservationGapClassification:
    """Apply the precedence order from the calendar gap specification."""
    if not trading_calendar_open:
        return ObservationGapClassification.EXPECTED_CALENDAR_GAP
    if tradability_status == "SUSPENDED":
        return ObservationGapClassification.SUSPENDED_TRADING_GAP
    if tradability_status is None or tradability_status == "UNKNOWN":
        return ObservationGapClassification.UNRESOLVED_GAP
    if valuation_expected:
        return ObservationGapClassification.DELAYED_OR_MISSING_VALUATION
    return ObservationGapClassification.UNRESOLVED_GAP


class ObservationGapReasonObservation(StrEnum):
    """A specific observation key that is missing from the current gap context."""

    SECURITY_MASTER = "SECURITY_MASTER"
    TRADING_DATE = "TRADING_DATE"
    VALUATION_DATE = "VALUATION_DATE"


def observation_gap_reason(
    security_id: str,
    observation_date: date,
    observation: Observation,
) -> ObservationGapReason:
    """Return the precedence-defined reason for one absent observation."""
    if security_id and observation.observation_date == observation_date:
        if observation.code.kind == "TRADING":
            return ObservationGapReason.MISSING_OR_UNKNOWN_TRADABILITY
        return ObservationGapReason.EXPECTED_VALUATION_DELAYED_OR_MISSING
    if security_id and observation.code.kind == "TRADING":
        return ObservationGapReason.MISSING_VALUATION_DATE
    return ObservationGapReason.MISSING_SECURITY_MASTER


@dataclass(frozen=True, slots=True)
class CalendarResolutionError:
    reason: Literal["missing", "ambiguous", "invalid_registry"]


@dataclass(frozen=True, slots=True)
class CalendarVersion:
    version_id: str
    market: str
    timezone: str
    valid_from: date
    valid_to: date
    kind: CalendarKind
    open_dates: frozenset[date] | None
    expected_dates: frozenset[date] | None

    def __post_init__(self) -> None:
        if self.valid_from > self.valid_to:
            raise ValueError("calendar validity must not be inverted")
        if not self.version_id or not self.market or not self.timezone:
            raise ValueError("calendar version identifiers must not be empty")
        if self.kind == "TRADING" and (not self.open_dates or self.expected_dates):
            raise ValueError("trading calendar requires exactly an open-date set")
        if self.kind == "VALUATION" and (not self.expected_dates or self.open_dates):
            raise ValueError("valuation calendar requires exactly an expected-date set")
        if any(self.valid_from > local_date > self.valid_to for local_date in self._own_dates()):
            raise ValueError("calendar dates must lie within their validity")

    def in_effect(self, local_date: date) -> bool:
        return self.valid_from <= local_date <= self.valid_to

    def _own_dates(self) -> frozenset[date]:
        assert self.open_dates is not None or self.expected_dates is not None
        if self.kind == "TRADING":
            assert self.open_dates is not None
            return self.open_dates
        assert self.expected_dates is not None
        return self.expected_dates

    def _local_date(self, timestamp: datetime) -> date:
        return timestamp.astimezone(ZoneInfo(self.timezone)).date()


@dataclass(frozen=True, slots=True)
class CalendarService:
    versions: tuple[CalendarVersion, ...]

    def observation_date(
        self,
        timestamp: datetime,
        *,
        kind: CalendarKind,
    ) -> Result[date, CalendarResolutionError]:
        if timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None:
            return Failure(CalendarResolutionError("invalid_registry"))
        applicable = [
            version
            for version in self.versions
            if version.kind == kind and version.in_effect(version._local_date(timestamp))
        ]
        if len(applicable) == 0:
            return Failure(CalendarResolutionError("missing"))
        if len(applicable) > 1:
            return Failure(CalendarResolutionError("ambiguous"))
        return Success(applicable[0]._local_date(timestamp))

    def open_dates(self, market: str) -> tuple[date, ...]:
        return _sorted_dates(
            _own_dates(
                [
                    version
                    for version in self.versions
                    if version.kind == "TRADING" and version.market == market
                ]
            )
        )

    def expected_dates(self, market: str) -> tuple[date, ...]:
        return _sorted_dates(
            _own_dates(
                [
                    version
                    for version in self.versions
                    if version.kind == "VALUATION" and version.market == market
                ]
            )
        )

    def is_open(self, market: str, candidate: date) -> bool:
        return candidate in _own_dates(
            [
                version
                for version in self.versions
                if version.kind == "TRADING" and version.market == market
            ]
        )

    def is_expected(self, market: str, candidate: date) -> bool:
        return candidate in _own_dates(
            [
                version
                for version in self.versions
                if version.kind == "VALUATION" and version.market == market
            ]
        )


def _own_dates(versions: list[CalendarVersion]) -> set[date]:
    result: set[date] = set()
    for version in versions:
        result.update(version._own_dates())
    return result


def _sorted_dates(dates: set[date]) -> tuple[date, ...]:
    return tuple(sorted(dates))
