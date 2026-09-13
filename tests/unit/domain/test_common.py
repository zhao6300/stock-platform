from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from stock_platform.domain.common import (
    Failure,
    Result,
    Success,
    canonical_json,
    canonical_value,
    ensure_timezone_aware,
    unpack,
)

_SUCCESS_VALUE = 41


def test_canonical_json_sorts_keys_and_represents_decimal_as_string() -> None:
    encoded = canonical_json(
        {"b": Decimal("1.2300"), "a": [datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)]}
    )

    assert encoded == '{"a":["2026-01-02T03:04:05+00:00"],"b":"1.23"}'


@pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), float("-inf"), Decimal("NaN"), object()]
)
def test_canonical_json_rejects_unsafe_values(value: object) -> None:
    with pytest.raises(ValueError, match=r"finite|unsupported"):
        canonical_value(value)


def test_result_is_a_closed_success_or_failure_discriminant() -> None:
    success: Result[int, RuntimeError] = Success(_SUCCESS_VALUE)
    failure: Result[int, ValueError] = Failure(ValueError("missing"))

    assert unpack(success) == _SUCCESS_VALUE
    with pytest.raises(ValueError, match="missing"):
        unpack(failure)


def test_timezone_awareness_is_required() -> None:
    assert ensure_timezone_aware(datetime(2026, 1, 1, tzinfo=UTC)).tzinfo is UTC
    with pytest.raises(ValueError, match="timezone-aware"):
        ensure_timezone_aware(datetime(2026, 1, 1))
