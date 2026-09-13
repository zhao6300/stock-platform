from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.common import Result, Success
from stock_platform.domain.ingestion import (
    ObservationRunCounts,
    ObservationRunOutcome,
    observation_run_counts,
)


def _outcome(category: int) -> ObservationRunOutcome:
    flags = [index == category for index in range(4)]
    return ObservationRunOutcome(*flags)


@given(
    categories=st.lists(
        st.integers(min_value=0, max_value=3),
        max_size=100,
    ),
)
def test_ingestion_counts_are_exclusive_and_conserved(
    categories: list[int],
) -> None:
    outcomes = [_outcome(category) for category in categories]
    result: Result[ObservationRunCounts, object] = observation_run_counts(
        len(outcomes),
        outcomes,
    )
    assert isinstance(result, Success)
    counts = result.value
    assert (
        counts.accepted + counts.warning + counts.rejected + counts.unresolved == counts.requested
    )
