from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from stock_platform.application.errors import ErrorCode
from stock_platform.application.policy import (
    MvpPolicy,
    UnsupportedCapability,
)
from stock_platform.domain.common import Failure, Success


def test_empty_request_is_allowed_as_research_only_daily_long_only() -> None:
    result = MvpPolicy.validate(set())

    assert isinstance(result, Success)
    assert result.value.periods == "DAILY"
    assert result.value.direction == "LONG_ONLY"
    assert result.value.leverage == "NONE"
    assert result.value.market_interaction == "RESEARCH_ONLY"

    with pytest.raises(FrozenInstanceError):
        result.value.periods = "MINUTE"  # type: ignore[assignment]


def test_all_requested_unsupported_capabilities_are_enumerated() -> None:
    requested = {
        UnsupportedCapability.SHORT_SELLING,
        UnsupportedCapability.BROKER_CONNECTION,
    }

    result = MvpPolicy.validate(requested)

    assert isinstance(result, Failure)
    assert result.error.code == ErrorCode.UNSUPPORTED_CAPABILITY
    assert set(result.error.context["unsupported"]) == {
        "broker connection",
        "short selling",
    }
