from __future__ import annotations

from datetime import date

from hypothesis import assume, given
from hypothesis import strategies as st

from stock_platform.domain.common import Failure, Success
from stock_platform.domain.identifiers import (
    AmbiguousIdentifier,
    IdentifierMapping,
    IdentityKey,
    IdentityRegistry,
    IdentityVersion,
    ResolvedIdentifier,
    UnresolvedIdentifier,
    _version_id,
)


@st.composite
def _provider_id_strategy(draw: st.DrawFn) -> str:
    return draw(st.text(min_size=1, max_size=15, alphabet="ABCDEF"))


def _identity(canonical_security_id: str, valid_from: date, local_code: str) -> IdentityVersion:
    return IdentityVersion(
        version_id=_version_id(canonical_security_id, valid_from),
        canonical_security_id=canonical_security_id,
        identity=IdentityKey(
            market="XSHG",
            instrument_type="A_Share",
            local_code=local_code,
            valid_from=valid_from,
        ),
        name=local_code,
        listing_date=date(2023, 1, 1),
        status="ACTIVE",
        currency="CNY",
        termination_date=None,
    )


@given(
    provider_id=_provider_id_strategy(),
    observation_date=st.dates(),
    provider_id2=_provider_id_strategy(),
    observation_date2=st.dates(),
)
def test_mapping_resolution_is_trichotomous(
    provider_id: str,
    observation_date: date,
    provider_id2: str,
    observation_date2: date,
) -> None:
    assume(provider_id != provider_id2)
    assume(observation_date != observation_date2)
    registry = IdentityRegistry()
    first = _identity("SEC-A", date(2026, 1, 1), "A")
    second = _identity("SEC-B", date(2026, 2, 1), "B")
    registry.register(first)
    registry.register(second)
    mapping = IdentifierMapping(
        provider="acme-a",
        provider_id=provider_id,
        canonical_security_id=first.canonical_security_id,
        valid_from=observation_date,
        valid_to=observation_date,
    )
    ambiguous = IdentifierMapping(
        provider="acme-a",
        provider_id=provider_id,
        canonical_security_id=second.canonical_security_id,
        valid_from=observation_date,
        valid_to=observation_date,
    )
    registry.register_mapping(mapping)
    assert registry.resolve("acme-a", provider_id, observation_date) == Success(
        ResolvedIdentifier(first.canonical_security_id)
    )
    assert registry.resolve("acme-a", provider_id2, observation_date2) == Failure(
        UnresolvedIdentifier("acme-a", provider_id2, observation_date2)
    )
    registry._mappings[f"acme-a:{provider_id}"] = [mapping, ambiguous]
    assert registry.resolve("acme-a", provider_id, observation_date) == Failure(
        AmbiguousIdentifier(
            (
                (first.canonical_security_id, observation_date, observation_date),
                (second.canonical_security_id, observation_date, observation_date),
            )
        )
    )
