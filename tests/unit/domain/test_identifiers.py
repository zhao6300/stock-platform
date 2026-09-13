from __future__ import annotations

from stock_platform.domain.identifiers import IdentifierMapping


def test_identifier_mapping_is_typed_by_market_and_identity() -> None:
    mapping = IdentifierMapping(
        provider="Acme",
        provider_name="Acme",
        provider_id="acme",
        canonical_security_id="",
    )
    assert mapping.canonical_security_id == ""
