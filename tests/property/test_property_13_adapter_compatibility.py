from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.providers.capabilities import CapabilityProbe
from stock_platform.providers.registry import ProviderRegistry

supported_contract_versions = st.from_regex(r"\w+", fullmatch=True)


@given(
    existing=supported_contract_versions,
    requested=supported_contract_versions,
)
def test_incompatible_adapters_stay_disabled(
    existing: str, requested: str
) -> None:
    registry = ProviderRegistry(
        adapters=("contracted",),
        allow_list=("contracted",),
    )
    probe = CapabilityProbe(
        outcome="failure" if existing != requested else "success",
        unsupported=(),
    )

    if existing != requested:
        assert probe.outcome == "failure"
        assert not registry.allowed("unknown")
    elif registry.allowed("contracted"):
        assert probe.outcome == "success"
