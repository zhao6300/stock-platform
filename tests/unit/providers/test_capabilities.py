from __future__ import annotations

import pytest

from stock_platform.providers.capabilities import CapabilityValue


def test_capability_kind() -> None:
    value = CapabilityValue("market", ("US",), True)
    assert value.rational_type == "market"


@pytest.mark.parametrize(
    "value",
    [(CapabilityValue("market", ("US",), True), ("US",), True)],
)
def test_capability_value(
    value: tuple[CapabilityValue, tuple[str, ...], bool],
) -> None:
    reported = value[0]
    assert reported.reported is True
    assert reported.rational_type == "market"
    assert reported.rational_value == value[1]
