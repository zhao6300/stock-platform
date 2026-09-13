from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from stock_platform.domain.common import ensure_timezone_aware
from stock_platform.domain.ingestion import DailyBar, FundNav


class QualityStatus(StrEnum):
    """The single most severe quality state for an observation."""

    VALID = "VALID"
    WARNING = "WARNING"
    REJECTED = "REJECTED"


class UnavailableInput(StrEnum):
    """Explicit quality rule inputs that remain unresolved at run time."""

    CALENDAR = "CALENDAR"
    SECURITY_MASTER = "SECURITY_MASTER"
    ADJUSTMENT_FACTOR = "ADJUSTMENT_FACTOR"
    OTHER = "OTHER"


_SEVERITY_RANK = {
    QualityStatus.VALID: 0,
    QualityStatus.WARNING: 1,
    QualityStatus.REJECTED: 2,
}




@dataclass(frozen=True, slots=True)
class QualityRule:
    """A versioned rule to assess canonical data quality."""

    rule_id: str
    version_id: str
    status: QualityStatus
    plan_impact: str = "BLOCK"
    provenance_level: str = "REGENERATABLE"
    remediation: str = "INVESTIGATE"


@dataclass(frozen=True, slots=True)
class QualityIssue:
    """Evidence needed to audit a rule failure."""

    security_id: str
    observation_date: date
    rule: QualityRule
    affected_field: str
    observed_value: str
    missing_input: UnavailableInput | None = None


@dataclass(frozen=True, slots=True)
class QualityReport:
    """A complete quality summary for a checked observation scope."""

    scope: str
    rule_version_id: str
    issues: tuple[QualityIssue, ...]
    generated_at: datetime

    def __post_init__(self) -> None:
        ensure_timezone_aware(self.generated_at)
        if not all(issue.rule.version_id == self.rule_version_id for issue in self.issues):
            raise ValueError("quality report issues must use the same rule version")
        if not self.scope:
            raise ValueError("quality report scope must not be blank")
        if not self.rule_version_id:
            raise ValueError("quality report rule version must not be blank")

    @property
    def status(self) -> QualityStatus:
        """Return the most severe status present in the report."""
        return (
            maximum_status(*(issue.rule.status for issue in self.issues))
            if self.issues
            else QualityStatus.VALID
        )

    @classmethod
    def from_scope(
        cls,
        *,
        scope: str,
        rule_version_id: str,
        issues: tuple[QualityIssue, ...],
        generated_at: datetime,
    ) -> QualityReport:
        """Return a quality report using an explicit rule version."""
        return cls(
            scope=scope,
            rule_version_id=rule_version_id,
            issues=issues,
            generated_at=generated_at,
        )


class QualityService:
    """A pure, reusable quality assessor for normalized observations."""

    def __init__(self, rule_version_id: str) -> None:
        self.rule_version_id = rule_version_id

    def validate_rule(self, rule: QualityRule, target: DailyBar | FundNav) -> None:
        """Reject a quality rule that targets out-of-scope data."""
        if rule.version_id != self.rule_version_id:
            raise ValueError("quality rule must use the configured rule version")
        if not isinstance(target, (DailyBar, FundNav)):
            raise ValueError("quality rule must target a Daily Bar or Fund NAV")

    def daily_bar_issues(
        self,
        daily_bar: DailyBar,
        security_id: str,
        *,
        open_on_calendar: bool | None = None,
    ) -> tuple[QualityIssue, ...]:
        """Return every failed Daily Bar quality check with complete evidence."""
        issues: list[QualityIssue] = []
        if open_on_calendar is None:
            issues.append(
                _issue(
                    "DAILY_BAR_CALENDAR",
                    security_id,
                    daily_bar.observation_date,
                    "observation_date",
                    "missing",
                    QualityStatus.WARNING,
                    self.rule_version_id,
                    UnavailableInput.CALENDAR,
                )
            )
        elif not open_on_calendar:
            issues.append(
                _issue(
                    "DAILY_BAR_CALENDAR",
                    security_id,
                    daily_bar.observation_date,
                    "observation_date",
                    str(daily_bar.observation_date),
                    QualityStatus.REJECTED,
                    self.rule_version_id,
                )
            )

        positive_fields = ("open", "high", "low", "close")
        nonnegative_fields = ("volume", "turnover")

        for field in positive_fields:
            value = _value(daily_bar, field)
            if not isinstance(value, Decimal) or value <= 0:
                issues.append(
                    _issue(
                        "DAILY_BAR_POSITIVE_PRICE",
                        security_id,
                        daily_bar.observation_date,
                        field,
                        str(value),
                        QualityStatus.REJECTED,
                        self.rule_version_id,
                    )
                )

        for field in nonnegative_fields:
            value = _value(daily_bar, field)
            if not isinstance(value, Decimal) or value < 0:
                issues.append(
                    _issue(
                        "DAILY_BAR_NON_NEGATIVE_TOTAL",
                        security_id,
                        daily_bar.observation_date,
                        field,
                        str(value),
                        QualityStatus.REJECTED,
                        self.rule_version_id,
                    )
                )

        open_price = _value(daily_bar, "open")
        high_price = _value(daily_bar, "high")
        low_price = _value(daily_bar, "low")
        close_price = _value(daily_bar, "close")
        if all(
            isinstance(value, Decimal) for value in (open_price, high_price, low_price, close_price)
        ):
            assert isinstance(open_price, Decimal)
            assert isinstance(high_price, Decimal)
            assert isinstance(low_price, Decimal)
            assert isinstance(close_price, Decimal)
            if (
                high_price < open_price
                or high_price < close_price
                or low_price > open_price
                or low_price > close_price
            ):
                issues.append(
                    _issue(
                        "DAILY_BAR_OHLC_STRUCTURE",
                        security_id,
                        daily_bar.observation_date,
                        "high_low",
                        f"open={open_price};high={high_price};low={low_price};close={close_price}",
                        QualityStatus.REJECTED,
                        self.rule_version_id,
                    )
                )

        return tuple(issues)

    def fund_nav_issues(
        self,
        fund_nav: FundNav,
        security_id: str,
        *,
        expected_on_calendar: bool | None = None,
    ) -> tuple[QualityIssue, ...]:
        """Return every failed fund NAV quality check with complete evidence."""
        issues: list[QualityIssue] = []
        if expected_on_calendar is None:
            issues.append(
                _issue(
                    "FUND_NAV_CALENDAR",
                    security_id,
                    fund_nav.observation_date,
                    "observation_date",
                    "missing",
                    QualityStatus.WARNING,
                    self.rule_version_id,
                    UnavailableInput.CALENDAR,
                )
            )
        elif not expected_on_calendar:
            issues.append(
                _issue(
                    "FUND_NAV_CALENDAR",
                    security_id,
                    fund_nav.observation_date,
                    "observation_date",
                    str(fund_nav.observation_date),
                    QualityStatus.REJECTED,
                    self.rule_version_id,
                )
            )

        for field in ("unit_nav", "cumulative_nav"):
            value = _value(fund_nav, field)
            if value is None:
                continue
            if not isinstance(value, Decimal) or value <= 0:
                issues.append(
                    _issue(
                        "FUND_NAV_POSITIVE_NAV",
                        security_id,
                        fund_nav.observation_date,
                        field,
                        str(value),
                        QualityStatus.REJECTED,
                        self.rule_version_id,
                    )
                )

        unit_nav = _value(fund_nav, "unit_nav")
        cumulative_nav = _value(fund_nav, "cumulative_nav")
        if (
            isinstance(unit_nav, Decimal)
            and isinstance(cumulative_nav, Decimal)
            and cumulative_nav < unit_nav
        ):
            issues.append(
                _issue(
                    "FUND_NAV_CUMULATIVE_GE_UNIT",
                    security_id,
                    fund_nav.observation_date,
                    "cumulative_nav",
                    f"unit_nav={unit_nav};cumulative_nav={cumulative_nav}",
                    QualityStatus.REJECTED,
                    self.rule_version_id,
                )
            )

        return tuple(issues)

    def report(
        self,
        scope: str,
        issues: tuple[QualityIssue, ...],
        *,
        generated_at: datetime,
    ) -> QualityReport:
        """Aggregate issue evidence into one immutable quality report."""
        return QualityReport(
            scope=scope,
            rule_version_id=self.rule_version_id,
            issues=issues,
            generated_at=generated_at,
        )

    @staticmethod
    def quality_report(
        scope: str,
        rule_version_id: str,
        issues: tuple[QualityIssue, ...],
        *,
        generated_at: datetime,
    ) -> QualityReport:
        """Return a quality report in one call for explicit rule versions."""
        return QualityReport(
            scope=scope,
            rule_version_id=rule_version_id,
            issues=issues,
            generated_at=generated_at,
        )



def _value(source: DailyBar | FundNav, field: str) -> Decimal | None:
    value = getattr(source, field)
    return value if value is None else Decimal(value)


def _issue(  # noqa: PLR0913
    rule_id: str,
    security_id: str,
    observation_date: date,
    affected_field: str,
    observed_value: str,
    status: QualityStatus,
    rule_version_id: str,
    missing_input: UnavailableInput | None = None,
) -> QualityIssue:
    return QualityIssue(
        security_id=security_id,
        observation_date=observation_date,
        affected_field=affected_field,
        observed_value=observed_value,
        rule=QualityRule(rule_id, rule_version_id, status),
        missing_input=missing_input,
    )


def maximum_status(*statuses: QualityStatus) -> QualityStatus:
    """Return the single most severe quality status."""
    return max(statuses, key=_SEVERITY_RANK.__getitem__)
