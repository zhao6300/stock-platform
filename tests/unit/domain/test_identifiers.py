from __future__ import annotations

from datetime import date

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from stock_platform.domain.common import Success
from stock_platform.domain.identifiers import (
    IdentifierMapping,
    IdentityKey,
    IdentityRegistry,
    IdentityVersion,
    ResolvedIdentifier,
    _version_id,
)

_INSTRUMENT_TYPES = ("A_Share", "HK_Equity", "ETF", "Open_End_Fund")
_STATUSES = ("ACTIVE", "SUSPENDED", "TERMINATED")


@st.composite
def _local_code(draw: st.DrawFn) -> str:
    return draw(st.text(alphabet="ABCDEF", min_size=1, max_size=12))


def _identity(local_code: str, status: str = "ACTIVE") -> IdentityVersion:
    key = IdentityKey(
        market="XSHG",
        instrument_type="A_Share",
        local_code=local_code,
        valid_from=date(2026, 1, 1),
    )
    canonical = IdentityRegistry._canonical_id(
        key.market,
        key.instrument_type,
        key.local_code,
    )
    return IdentityVersion(
        version_id=_version_id(canonical, key.valid_from),
        canonical_security_id=canonical,
        identity=key,
        name=local_code,
        listing_date=date(2023, 1, 1),
        status=status,  # type: ignore[arg-type]
        currency="CNY",
        termination_date=None,
    )


@given(first_key=_local_code(), second_key=_local_code(), status=st.sampled_from(_STATUSES))
def test_identity_registry_stable_ids_use_three_component_keys(
    first_key: str,
    second_key: str,
    status: str,
) -> None:
    assume(first_key != second_key)
    registry = IdentityRegistry()
    first = _identity(first_key, "ACTIVE")
    registry.register(first)
    registry.register(_identity(second_key, status))
    assert first.canonical_security_id == registry._canonical_id(
        first.identity.market,
        first.identity.instrument_type,
        first.identity.local_code,
    )
    assert len(registry.identity_history(first.canonical_security_id)) == 1
    assert len(registry.mapping_history("Acme", "ACME-1")) == 0


def test_invalid_identity_is_rejected() -> None:
    with pytest.raises(ValueError):
        IdentityKey(
            market="XSHG", instrument_type="A_Share", local_code="", valid_from=date(2026, 1, 1)
        )


@given(first_key=_local_code(), second_key=_local_code())
def test_mapping_resolution_is_trichotomous(first_key: str, second_key: str) -> None:
    assume(first_key != second_key)
    registry = IdentityRegistry()
    first = _identity(first_key, "ACTIVE")
    second = _identity(second_key, "ACTIVE")
    registry.register(first)
    registry.register(second)
    mapping = IdentifierMapping(
        provider="Acme",
        provider_id="ACME-1",
        canonical_security_id=first.canonical_security_id,
        valid_from=date(2026, 1, 1),
        valid_to=date(2026, 12, 31),
    )
    registry.register_mapping(mapping)
    assert registry.resolve("Acme", "ACME-1", date(2026, 3, 1)) == Success(
        ResolvedIdentifier(first.canonical_security_id)
    )
