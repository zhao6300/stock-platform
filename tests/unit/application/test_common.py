from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from stock_platform.application.dto import DTO
from stock_platform.application.errors import ErrorCode, ErrorEnvelope


@dataclass(frozen=True, slots=True)
class ExampleDTO(DTO):
    name: str
    amount: Decimal


def test_dto_is_frozen_and_serializes_canonical_scalars() -> None:
    value = ExampleDTO(name="example", amount=Decimal("1.20"))

    assert value.amount == Decimal("1.20")
    with pytest.raises(AttributeError):
        value.name = "changed"  # type: ignore[misc]
    assert value.as_dict() == {"amount": "1.2", "name": "example"}


def test_error_envelope_requires_timezone_and_safe_context() -> None:
    envelope = ErrorEnvelope.build(
        ErrorCode.VALIDATION_FAILED,
        "range is invalid",
        {"start_date": "2026-01-01"},
        timestamp=datetime(2026, 9, 13, 5, 30, tzinfo=UTC),
    )

    assert envelope.code == ErrorCode.VALIDATION_FAILED
    assert envelope.context == {"start_date": "2026-01-01"}
    with pytest.raises(ValueError, match="timezone-aware"):
        ErrorEnvelope(
            code=ErrorCode.INTERNAL,
            message="bad time",
            context={},
            timestamp=datetime(2026, 9, 13),
        )
    with pytest.raises(ValueError, match="message"):
        ErrorEnvelope.build(ErrorCode.INTERNAL, "")
