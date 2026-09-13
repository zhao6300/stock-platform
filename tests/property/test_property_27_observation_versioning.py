from __future__ import annotations

from datetime import date
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.ingestion import (
    ObservationVersion,
    VersionDecision,
    decide_observation_version,
)


@given(
    version_id_client=st.text(min_size=1, max_size=30),
    predecessor_id=st.one_of(st.none(), st.text(min_size=1, max_size=30)),
    close=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("1e12")),
)
def test_observation_versioning_is_idempotent_and_linear(
    version_id_client: str,
    predecessor_id: str | None,
    close: Decimal,
) -> None:
    current = ObservationVersion(
        version_id="stored-v1",
        security_id="SEC-1",
        data_type="DailyBar",
        observation_date=date(2026, 1, 2),
        field_values=frozenset((("close", str(close)),)),
        predecessor_id=predecessor_id,
    )
    unchanged = ObservationVersion(
        version_id=version_id_client,
        security_id="SEC-1",
        data_type="DailyBar",
        observation_date=date(2026, 1, 2),
        field_values=current.field_values,
    )
    changed = ObservationVersion(
        version_id="incoming-v2",
        security_id="SEC-1",
        data_type="DailyBar",
        observation_date=date(2026, 1, 2),
        field_values=frozenset((("close", str(close + Decimal("1"))),)),
    )

    assert decide_observation_version(current, unchanged) == VersionDecision(
        False,
        "stored-v1",
        predecessor_id,
    )
    assert decide_observation_version(current, changed) == VersionDecision(
        True,
        "incoming-v2",
        "stored-v1",
    )
