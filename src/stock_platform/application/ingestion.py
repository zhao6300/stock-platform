from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from stock_platform.domain.common import Failure, Result, Success
from stock_platform.domain.ingestion import (
    IngestionPlan,
    ObservationRunCounts,
    ObservationRunOutcome,
    ObservationVersion,
    VersionDecision,
    observation_run_counts,
    planned_ingestion_dates,
    storage_preflight,
)
from stock_platform.domain.quality import (
    QualityReport,
    QualityStatus,
)

type Observation = Any


def decide_observation_version(
    current: ObservationVersion | None,
    candidate: ObservationVersion | None,
) -> VersionDecision | None:
    """Reuse an existing version, or append a direct child for changed values."""
    if candidate is None:
        return None
    if current is not None and current.field_values == candidate.field_values:
        return VersionDecision(False, current.version_id, current.predecessor_id)
    return VersionDecision(True, candidate.version_id, current.version_id if current else None)


@dataclass(frozen=True, slots=True)
class _ProviderResult:
    provider: object
    category: str
    candidate_dates: tuple[date, ...]
    correlation_id: str | None = None


class IngestionStatus(StrEnum):
    COMPLETED = "COMPLETED"
    INCOMPLETE = "INCOMPLETE"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class IngestionOperation:
    request_id: str
    dates: tuple[date, ...]
    storage_estimate: int
    storage_available: int
    finalized_before: frozenset[date] = frozenset()
    start: date | None = None
    end: date | None = None
    visible_dates: frozenset[date] = frozenset()
    waiting_for_pricing: frozenset[date] = frozenset()
    no_tradability: frozenset[date] = frozenset()
    insufficient_cash: frozenset[date] = frozenset()
    over_delivery: frozenset[date] = frozenset()
    provisional_dates: frozenset[date] = frozenset()
    published_dates: frozenset[date] = frozenset()
    refresh: bool = False
    provider_request: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProviderFailure:
    provider: object
    category: str
    candidate_dates: tuple[date, ...]
    correlation_id: str | None = None


class MissingFieldError(Exception):
    def __init__(self, fields: set[str]) -> None:
        self.fields = fields
        super().__init__(f"missing required fields: {sorted(fields)}")


@dataclass(frozen=True, slots=True)
class PublicationFailure:
    observation_date: date | None = None
    message: str | None = None


@dataclass(frozen=True, slots=True)
class PublicationFailures:
    observation_date: date


@dataclass(frozen=True, slots=True)
class IngestionRunFailure:
    provider_failures: tuple[ProviderFailure, ...] = ()
    publication_failures: tuple[PublicationFailure, ...] = ()
    finalized_dates: frozenset[date] = frozenset()
    resumable_boundary: date | None = None
    value: IngestionRunSummary | None = None

    @property
    def price_dates(self) -> frozenset[date]:
        return self.value.finalized_dates if self.value is not None else frozenset()

    @property
    def summary(self) -> IngestionRunSummary | None:
        return self.value


@dataclass(frozen=True, slots=True)
class IngestionRunSummary:
    plan: IngestionPlan
    status: IngestionStatus
    counts: ObservationRunCounts | None
    finalized_dates: frozenset[date]
    resumable_boundary: date | None
    quality_reports: tuple[QualityReport, ...]
    version_decisions: tuple[VersionDecision, ...]
    provider_failures: tuple[ProviderFailure, ...] = ()
    publication_failures: tuple[PublicationFailure, ...] = ()


@runtime_checkable
class IngestionPorts(Protocol):
    def provider_fetch(
        self, request: Any, observation_date: date
    ) -> Result[Any, ProviderFailure]: ...

    def normalize(self, envelope: Any) -> Result[Observation, MissingFieldError]: ...

    def quality_assess(self, observation: Observation) -> QualityReport: ...

    def current_version(self, observation: Observation) -> ObservationVersion | None: ...

    def candidate_version(
        self, observation: Observation
    ) -> ObservationVersion: ...

    def publish(
        self, current: ObservationVersion | None, candidate: ObservationVersion, report: QualityReport
    ) -> Result[Observation, PublicationFailure]: ...


@dataclass(frozen=True, slots=True)
class FinalizedIngestionRun:
    """Finalized dates, conserved counts, and one resume boundary."""

    completed: bool
    counts: ObservationRunCounts
    finalized_dates: frozenset[date]
    resumable_boundary: date | None


def finalize_ingestion_run(
    requested_dates: Sequence[date],
    outcomes: Sequence[ObservationRunOutcome],
    finalized_dates: frozenset[date],
) -> Result[FinalizedIngestionRun, str]:
    """Finalize only observations whose counts are conserved and strict."""
    counts_result = observation_run_counts(len(requested_dates), outcomes)
    if isinstance(counts_result, Failure):
        return Failure(counts_result.error.requested)

    counts = counts_result.value
    completed = counts.accepted == counts.requested
    finalized_set = finalized_dates if completed else frozenset()
    pending = frozenset(requested_dates) - finalized_set
    boundary = min(pending) if pending else None
    return Success(
        FinalizedIngestionRun(
            completed=completed,
            counts=counts,
            finalized_dates=finalized_set,
            resumable_boundary=boundary,
        )
    )


async def run_ingestion(
    operation: IngestionOperation, ports: IngestionPorts
) -> Result[IngestionRunSummary, IngestionRunFailure]:
    """Execute one strict, idempotent ingestion run and never publish partial invalid output."""
    start = operation.start if operation.start is not None else min(operation.dates)
    end = operation.end if operation.end is not None else max(operation.dates)
    plan_result = planned_ingestion_dates(
        operation.dates,
        tuple(operation.finalized_before),
        start=start,
        end=end,
        refresh=operation.refresh,
    )
    if isinstance(plan_result, Failure):
        return Success(
            IngestionRunSummary(
                plan=IngestionPlan("invalid", (), None),
                status=IngestionStatus.FAILED,
                counts=None,
                finalized_dates=frozenset(operation.finalized_before),
                resumable_boundary=None,
                quality_reports=(),
                version_decisions=(),
            )
        )

    plan = plan_result.value
    if not plan.requested_dates:
        return Success(
            IngestionRunSummary(
                plan=plan,
                status=IngestionStatus.COMPLETED,
                counts=None,
            finalized_dates=frozenset(operation.finalized_before),
                resumable_boundary=None,
                quality_reports=(),
                version_decisions=(),
            )
        )

    preflight_result = storage_preflight(
        operation.storage_estimate,
        operation.storage_available,
        list(operation.visible_dates) if operation.visible_dates else plan.requested_dates,
    )
    if isinstance(preflight_result, Failure):
        return Failure(
            IngestionRunFailure(
                finalized_dates=frozenset(operation.finalized_before),
                resumable_boundary=min(plan.requested_dates),
            )
        )

    outcomes: list[ObservationRunOutcome] = []
    finalized_dates: set[date] = set(operation.finalized_before)
    preflight_dates = preflight_result.value
    candidate_dates = set() if isinstance(preflight_dates, int) else set(preflight_dates)
    quality_reports: list[QualityReport] = []
    version_decisions: list[VersionDecision] = []
    provider_failures: list[ProviderFailure] = []
    publication_failures: list[PublicationFailure] = []
    stopped = False
    for observation_date in plan.requested_dates:
        if stopped:
            outcomes.append(ObservationRunOutcome(False, False, False, True))
            continue

        fetch_result = ports.provider_fetch(operation.provider_request, observation_date)
        if isinstance(fetch_result, Failure):
            provider_failures.append(fetch_result.error)
            stopped = True
            outcomes.append(ObservationRunOutcome(False, False, False, True))
            continue

        normalized_result = ports.normalize(fetch_result.value)
        if isinstance(normalized_result, Failure):
            finalized_dates.add(observation_date)
            outcomes.append(ObservationRunOutcome(False, False, True, False))
            continue

        observation = normalized_result.value
        quality_report = ports.quality_assess(observation)
        quality_reports.append(quality_report)
        current = ports.current_version(observation)
        candidate = ports.candidate_version(observation)
        if candidate is not None:
            decision = decide_observation_version(candidate, current)
            if decision is not None:
                version_decisions.append(decision)

        if not quality_report.issues:
            outcome = ObservationRunOutcome(True, False, False, False)
        elif any(
            issue.rule.status is QualityStatus.REJECTED for issue in quality_report.issues
        ):
            outcome = ObservationRunOutcome(False, False, True, False)
        else:
            outcome = ObservationRunOutcome(False, True, False, False)
        outcomes.append(outcome)
        if quality_report.issues:
            continue

        publication_result = ports.publish(current, candidate, quality_report)
        if isinstance(publication_result, Failure):
            publication_failures.append(publication_result.error)
            outcomes.pop()
            outcomes.append(ObservationRunOutcome(False, False, False, True))
            continue
        finalized_date = observation_date
        outcomes.pop()
        outcomes.append(ObservationRunOutcome(True, False, False, False))
        finalized_dates.add(finalized_date)

    counts_result = observation_run_counts(len(plan.requested_dates), outcomes)
    if isinstance(counts_result, Failure):
        return Failure(
            IngestionRunFailure(finalized_dates=frozenset(finalized_dates))
        )
    counts = counts_result.value

    rejected_count = sum(outcome.rejected for outcome in outcomes)
    unresolved_count = sum(outcome.unresolved for outcome in outcomes)
    warning_count = sum(outcome.warning for outcome in outcomes)
    status = IngestionStatus.COMPLETED
    if unresolved_count:
        status = IngestionStatus.INCOMPLETE
    elif warning_count or rejected_count:
        status = IngestionStatus.FAILED

    if publication_failures:
        finalized_dates |= candidate_dates - {
            failure.observation_date
            for failure in publication_failures
            if failure.observation_date is not None
        }
    pending = set(plan.requested_dates) - finalized_dates
    boundary = min(pending) if pending else None
    summary = IngestionRunSummary(
        plan=plan,
        status=status,
        counts=counts,
        finalized_dates=frozenset(finalized_dates),
        resumable_boundary=boundary,
        quality_reports=tuple(quality_reports),
        version_decisions=tuple(version_decisions),
    )
    if provider_failures or publication_failures:
        failure = IngestionRunFailure(
            provider_failures=tuple(provider_failures),
            publication_failures=tuple(publication_failures),
            finalized_dates=frozenset(finalized_dates),
            resumable_boundary=boundary,
            value=summary,
        )
        return Failure(failure)
    return Success(summary)
