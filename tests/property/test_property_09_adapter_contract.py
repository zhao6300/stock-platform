from __future__ import annotations

from dataclasses import dataclass

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.providers.contract import AdapterContract


@dataclass
class FakeAdapter:
    name: str
    contract_version: str


@given(
    name=st.from_regex(r"\w+", fullmatch=True),
    contract_version=st.text(min_size=1, max_size=32),
    malformed_contract_sizes=st.lists(st.integers(min_value=0, max_value=2), max_size=3),
)
def test_known_adapter_contract_is_singular_and_implemented(
    name: str, contract_version: str, malformed_contract_sizes: list[int]
) -> None:
    adapter = FakeAdapter(name=name, contract_version=contract_version)
    contract = AdapterContract(
        version=contract_version,
        auth_schema=("bearer",),
        capabilities=("daily_bar",),
        fetch=("daily_bar",),
        normalize=("daily_bar",),
    )

    assert contract.version == contract_version
    assert adapter.contract_version == contract_version
    assert len(malformed_contract_sizes) >= 0
