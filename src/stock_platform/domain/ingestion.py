from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from hashlib import sha256

from stock_platform.domain.common import Failure, Result, Success

type Numeric = Decimal | None


@dataclass(frozen=True, slots=True)
class IngestionPlan:
    """The stable dataset version and its pending request dates."""

    version_id: str
    requested_dates: tuple[date, ...]
    run_version_id: str | None = None


@dataclass(frozen=True, slots=True)
class ObservationRunOutcome:
    """Equivalent finalized observation classifications for a provider run."""

    accepted: bool
    warning: bool
    rejected: bool
    unresolved: bool


@dataclass(frozen=True, slots=True)
class ObservationRunCounts:
    """Mutually exclusive counts whose sum equals the requested count."""

    requested: int
    accepted: int
    warning: int
    rejected: int
    unresolved: int


@dataclass(frozen=True, slots=True)
class RunOutcomeValidationError:
    """An ingestion run request has an invalid outcome."""

    requested: str


def _count_sequences(
    outcomes: Sequence[ObservationRunOutcome],
) -> tuple[int, int, int, int]:
    return (
        sum(outcome.accepted for outcome in outcomes),
        sum(outcome.warning for outcome in outcomes),
        sum(outcome.rejected for outcome in outcomes),
        _count_true(outcomes, "unresolved"),
    )


def _count_true(
    outcomes: Sequence[ObservationRunOutcome], attribute: str
) -> int:
    return sum(getattr(outcome, attribute) for outcome in outcomes)


def observation_run_counts(
    requested: int, outcomes: Sequence[ObservationRunOutcome]
) -> Result[ObservationRunCounts, RunOutcomeValidationError]:
    """Return anonymized result counts with distinct, exactly-covered statuses."""
    if requested < 0:
        return Failure(RunOutcomeValidationError("requested"))
    accepted, warning, rejected, unresolved = _count_sequences(outcomes)
    requested_count = len(outcomes) if requested == 0 else requested
    totals = ObservationRunCounts(
        requested=requested_count,
        accepted=accepted,
        warning=warning,
        rejected=rejected,
        unresolved=unresolved,
    )
    if totals.accepted + totals.warning + totals.rejected + totals.unresolved != requested:
        return Failure(RunOutcomeValidationError("requested"))
    return Success(totals)


@dataclass(frozen=True, slots=True)
class ObservationVersion:
    """A stored normalized observation and its predecessor, when replaced."""

    version_id: str
    security_id: str
    data_type: str
    observation_date: date
    field_values: frozenset[tuple[str, str]]
    predecessor_id: str | None = None


@dataclass(frozen=True, slots=True)
class VersionDecision:
    """One idempotent decision: reuse the current version or append one child."""

    version_is_new: bool
    version_id: str
    predecessor_id: str | None


def decide_observation_version(
    current: ObservationVersion, incoming: ObservationVersion
) -> VersionDecision:
    """Compare logical-keyed observations and append only versioned changes."""
    if (
        current.security_id != incoming.security_id
        or current.data_type != incoming.data_type
        or current.observation_date != incoming.observation_date
    ):
        raise ValueError("observations must share the same logical identity")
    if current.field_values == incoming.field_values:
        return VersionDecision(False, current.version_id, current.predecessor_id)
    return VersionDecision(True, incoming.version_id, current.version_id)


__all__ = (
    "DailyBar",
    "DailyBarCandidate",
    "DailyBarValidationError",
    "FundNav",
    "FundNavCandidate",
    "FundNavValidationError",
)


@dataclass(frozen=True, slots=True)
class DailyBar:
    """Canonical daily price and volume facts."""

    observation_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    turnover: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class DailyBarValidationError:
    """A row-level rejection with every failing canonical field."""

    fields: frozenset[str]


@dataclass(frozen=True, slots=True)
class FundNav:
    """Canonical fund NAV facts."""

    observation_date: date
    unit_nav: Decimal
    cumulative_nav: Decimal | None
    currency: str


@dataclass(frozen=True, slots=True)
class FundNavValidationError:
    fields: frozenset[str]


@dataclass(frozen=True, slots=True)
class DailyBarCandidate:
    """A daily bar in provider-supplied units before canonical validation."""

    observation_date: date
    open: Numeric
    high: Numeric
    low: Numeric
    close: Numeric
    volume: Numeric
    turnover: Numeric
    currency: str

    @property
    def high_low_mismatch(self) -> bool:
        values = (self.open, self.low, self.close)
        return any(
            value is not None
            and (
                (self.high is not None and self.high < value)
                or (self.low is not None and self.low > value)
            )
            for value in values
        )

    @property
    def is_price_positive(self) -> bool:
        return all(
            value is not None and value > 0
            for value in (self.open, self.high, self.low, self.close)
        )

    @property
    def is_turnover_nonnegative(self) -> bool:
        return all(value is not None and value >= 0 for value in (self.volume, self.turnover))

    @property
    def is_currency_valid(self) -> bool:
        return bool(self.currency)


@dataclass(frozen=True, slots=True)
class FundNavCandidate:
    """A canonical fund NAV row with optional provider cumulative value."""

    observation_date: date
    unit_nav: Numeric
    cumulative_nav: Numeric = None
    currency: str = ""

    @property
    def cumulative_nav_mismatch(self) -> bool:
        return (
            self.unit_nav is not None
            and self.cumulative_nav is not None
            and self.cumulative_nav < self.unit_nav
        )


def normalize_daily_bar(
    candidate: DailyBarCandidate, currency: str
) -> Result[DailyBar, DailyBarValidationError]:
    """Validate a raw Daily Bar and return an all-or-nothing canonical row."""

    required_fields = ("open", "high", "low", "close", "volume", "turnover")
    if any(getattr(candidate, field) is None for field in required_fields):
        return Failure(DailyBarValidationError(frozenset(required_fields)))
    if not candidate.is_price_positive:
        return Failure(DailyBarValidationError(frozenset(required_fields)))
    if not candidate.is_turnover_nonnegative:
        return Failure(DailyBarValidationError(frozenset(required_fields)))
    if candidate.high_low_mismatch:
        return Failure(DailyBarValidationError(frozenset(required_fields)))

    return Success(
        DailyBar(
            observation_date=candidate.observation_date,
            open=candidate.open if candidate.open is not None else Decimal("0"),
            high=candidate.high if candidate.high is not None else Decimal("0"),
            low=candidate.low if candidate.low is not None else Decimal("0"),
            close=candidate.close if candidate.close is not None else Decimal("0"),
            volume=candidate.volume if candidate.volume is not None else Decimal("0"),
            turnover=candidate.turnover if candidate.turnover is not None else Decimal("0"),
            currency=currency,
        )
    )


def normalize_fund_nav(
    candidate: FundNavCandidate, currency: str
) -> Result[FundNav, FundNavValidationError]:
    """Validate a raw Fund NAV and return an all-or-nothing canonical row."""

    if candidate.unit_nav is None or candidate.unit_nav <= 0:
        return Failure(FundNavValidationError(frozenset(("unit_nav",))))
    if candidate.cumulative_nav is not None and candidate.cumulative_nav < candidate.unit_nav:
        return Failure(FundNavValidationError(frozenset(("cumulative_nav",))))

    return Success(
        FundNav(
            observation_date=candidate.observation_date,
            unit_nav=candidate.unit_nav,
            cumulative_nav=(
                candidate.cumulative_nav if candidate.cumulative_nav is not None else None
            ),
            currency=currency,
        )
    )


@dataclass(frozen=True, slots=True)
class IngestionRangeError:
    """A date range cannot produce a bounded ingestion request."""

    reason: str


def planned_ingestion_dates(
    expected_dates: Sequence[date],
    existing_dates: Sequence[date],
    *,
    start: date,
    end: date,
    refresh: bool = False,
) -> Result[IngestionPlan, IngestionRangeError]:
    """Select all expected observations for refresh, or absent segment dates."""
    if start > end:
        return Failure(IngestionRangeError("inverted"))

    candidates = sorted(d for d in expected_dates if start <= d <= end)
    dataset_signature = "|".join(
        (
            f"{start.isoformat()}::{end.isoformat()}",
            "refresh" if refresh else "incremental",
            ",".join(d.isoformat() for d in sorted(candidates)),
            ",".join(d.isoformat() for d in sorted(existing_dates)),
        )
    )
    missing_dates = (
        tuple(candidates)
        if refresh
        else tuple(d for d in candidates if d not in frozenset(existing_dates))
    )
    return Success(
        IngestionPlan(f"dataset-v1:{sha256(dataset_signature.encode()).hexdigest()}", missing_dates)
    )


@dataclass(frozen=True, slots=True)
class PreflightError:
    """All-or-nothing storage preflight evidence."""

    estimated_bytes: int
    available_bytes: int


def storage_preflight(
    estimated_bytes: int,
    available_bytes: int,
    candidate_dates: Sequence[date] | int,
) -> Result[Sequence[date] | int, PreflightError]:
    """Treat storage as exactly sufficient only when numeric bytes match."""
    if estimated_bytes < 0 or available_bytes < 0:
        raise ValueError("preflight byte counts must be non-negative")
    if available_bytes < estimated_bytes:
        return Failure(
            PreflightError(
                estimated_bytes=estimated_bytes,
                available_bytes=available_bytes,
            )
        )
    return Success(candidate_dates)
