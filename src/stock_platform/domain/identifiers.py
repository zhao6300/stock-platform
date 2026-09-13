from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

type IdentityStatus = Literal["ACTIVE", "SUSPENDED", "TERMINATED"]


@dataclass(frozen=True, slots=True)
class IdentifierMapping:
    """A canonical ID associated with a named market provider identity."""

    provider: str
    provider_name: str
    canonical_security_id: str
    provider_id: str

@dataclass(frozen=True, slots=True)
class IdentityVersion:
    """A strongly typed market security identity."""

    version_id: str
    canonical_security_id: str
    identity: IdentityKey
    name: str
    listing_date: date
    status: IdentityStatus
    currency: str
    termination_date: date | None

    def __post_init__(self) -> None:
        if not self.canonical_security_id or not self.version_id:
            raise ValueError("identity identifiers must not be blank")

@dataclass(frozen=True, slots=True)
class IdentityKey:
    market: str
    instrument_type: str
    local_code: str
    valid_from: date
    valid_to: date | None = None

@dataclass(frozen=True, slots=True)
class IdentityRegistry:
    bindings: dict[IdentityKey, IdentityVersion]

    def register(self, version: IdentityVersion) -> None:
        canonical_id = _canonical_id(version.identity.market, version.identity.instrument_type, version.identity.local_code)
        version_id = _version_id(canonical_id, version.identity.valid_from)
        current = replace(version, canonical_security_id=canonical_id, version_id=version_id)
        self.bindings[current.identity] = current

    @property
    def identity(self) -> IdentityVersion:
        for version_id in self.bindings.values():
            return version_id
        raise ValueError("empty registry")

def _canonical_id(market: str, instrument_type: str, local_code: str) -> str:
    key = f"{market}:{instrument_type}:{local_code}"
    return f"urn:stock-research:{market}:{instrument_type}:{uuid5(NAMESPACE_URL, key)}"

def _version_id(canonical_id: str, valid_from: date) -> str:
    return uuid5(NAMESPACE_URL, f"{canonical_id}:{valid_from}").hex
