from __future__ import annotations

from dataclasses import dataclass

from stock_platform.providers.capabilities import CapabilityProbe

_SUPPORTED_CONTRACT_VERSION = "1.1"


@dataclass(frozen=True, slots=True)
class ProviderContractState:
    enabled: bool
    declared_version: str
    supported_version: str
    requests_allowed: bool


def request_allowed_for_adapter_contract(
    declared_version: str,
    *,
    supported_version: str = _SUPPORTED_CONTRACT_VERSION,
    probe: CapabilityProbe | None = None,
) -> ProviderContractState:
    """Translate an adapter version and capability probe to a request boundary."""

    compatible = declared_version == supported_version
    probe_success = probe is None or probe.outcome == "success"
    enabled = compatible and probe_success
    return ProviderContractState(
        enabled=enabled,
        declared_version=declared_version,
        supported_version=supported_version,
        requests_allowed=enabled,
    )


def replacement_adapter_state(
    previous_adapter: str,
    next_adapter: str,
    probe: CapabilityProbe,
    *,
    current_enabled: bool,
) -> tuple[str, str]:
    """Return exactly one enabled adapter after a replacement attempt."""

    if probe.outcome == "success" and current_enabled:
        return previous_adapter, next_adapter
    return previous_adapter, previous_adapter
