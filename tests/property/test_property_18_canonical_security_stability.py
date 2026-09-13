from __future__ import annotations

from dataclasses import replace
from datetime import date

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.identifiers import (
    IdentityKey,
    IdentityRegistry,
    IdentityVersion,
    _version_id,
)

_HISTORY_VERSION_COUNT = 2


@st.composite
def _identity_code(draw: st.DrawFn) -> str:
    return draw(st.text(alphabet="ABCDEF", min_size=1, max_size=10))


@given(local_code=_identity_code(), status=st.sampled_from(("ACTIVE", "SUSPENDED", "TERMINATED")))
def test_lifecycle_change_preserves_the_canonical_identifier(
    local_code: str,
    status: str,
) -> None:
    registry = IdentityRegistry()
    key = IdentityKey(
        market="XSHG",
        instrument_type="A_Share",
        local_code=local_code,
        valid_from=date(2026, 1, 1),
    )
    canonical = IdentityRegistry._canonical_id(key.market, key.instrument_type, key.local_code)
    first = IdentityVersion(
        version_id=_version_id(canonical, key.valid_from),
        canonical_security_id=canonical,
        identity=key,
        name=local_code,
        listing_date=date(2023, 1, 1),
        status="ACTIVE",
        currency="CNY",
        termination_date=None,
    )
    registry.register(first)
    second = replace(first, status=status, identity=replace(key, valid_from=date(2026, 1, 2)))  # type: ignore[arg-type]
    registry.register(second)
    assert first.canonical_security_id == canonical
    assert second.canonical_security_id == canonical
    assert len(registry.identity_history(canonical)) == _HISTORY_VERSION_COUNT
