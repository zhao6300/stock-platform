from __future__ import annotations

import pytest

from stock_platform.application.providers import (
    ProviderContractState,
    request_allowed_for_adapter_contract,
)
from stock_platform.providers.capabilities import CapabilityProbe


def test_adapter_contract_state_is_compatible_and_request_allowed() -> None:
    state = request_allowed_for_adapter_contract("1.1")

    assert state == ProviderContractState(
        enabled=True,
        declared_version="1.1",
        supported_version="1.1",
        requests_allowed=True,
    )


@pytest.mark.parametrize(
    ("declared", "supported", "outcome", "enabled"),
    [
        ("1.0", "1.1", "success", False),
        ("1.1", "1.1", "failure", False),
        ("1.1", "1.1", "success", True),
    ],
)
def test_adapter_request_boundary_prevents_gateways(
    declared: str,
    supported: str,
    outcome: str,
    enabled: bool,
) -> None:
    state = request_allowed_for_adapter_contract(
        declared,
        supported_version=supported,
        probe=CapabilityProbe(outcome=outcome, unsupported=()),
    )

    assert state.enabled is enabled
    assert state.requests_allowed is enabled
