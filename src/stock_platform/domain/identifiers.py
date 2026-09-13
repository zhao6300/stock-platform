from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

from stock_platform.domain.common import Failure, Result, Success

type InstrumentType = Literal["A_Share", "HK_Equity", "ETF", "Open_End_Fund"]
type IdentityStatus = Literal["ACTIVE", "SUSPENDED", "TERMINATED"]

_INSTRUMENT_TYPES = frozenset({"A_Share", "HK_Equity", "ETF", "Open_End_Fund"})
_IDENTITY_STATUSES = frozenset({"ACTIVE", "SUSPENDED", "TERMINATED"})
_MAXIMUM_PROVIDER_ID_LENGTH = 255


@dataclass(frozen=True, slots=True)
class IdentityKey:
    market: str
    instrument_type: InstrumentType
    local_code: str
    valid_from: date
    valid_to: date | None = None

    def __post_init__(self) -> None:
        if not self.market or not self.local_code:
            raise ValueError("market and local code must not be blank")
        if self.instrument_type not in _INSTRUMENT_TYPES:
            raise ValueError("instrument type is unsupported")
        if self.valid_to is not None and self.valid_from > self.valid_to:
            raise ValueError("identity validity is inverted")


@dataclass(frozen=True, slots=True)
class IdentityVersion:
    version_id: str
    canonical_security_id: str
    identity: IdentityKey
    name: str
    listing_date: date
    status: IdentityStatus
    currency: str
    termination_date: date | None

    def __post_init__(self) -> None:
        if not self.version_id or not self.canonical_security_id:
            raise ValueError("identity identifiers must not be blank")
        if not self.name or not self.currency:
            raise ValueError("name and currency must not be blank")
        if self.status not in _IDENTITY_STATUSES:
            raise ValueError("identity status is unsupported")
        if self.termination_date is not None and self.identity.valid_from > self.termination_date:
            raise ValueError("termination precedes identity validity")


@dataclass(frozen=True, slots=True)
class IdentifierMapping:
    provider: str
    provider_id: str
    canonical_security_id: str
    valid_from: date
    valid_to: date
    mapping_id: str = ""

    def __post_init__(self) -> None:
        if not 1 <= len(self.provider_id) <= _MAXIMUM_PROVIDER_ID_LENGTH:
            raise ValueError("provider identifier length is outside 1..255")
        if not self.provider or not self.provider_id or not self.canonical_security_id:
            raise ValueError("mapping identifiers must not be blank")
        if self.valid_from > self.valid_to:
            raise ValueError("mapping validity is inverted")


@dataclass(frozen=True, slots=True)
class ResolvedIdentifier:
    canonical_security_id: str


@dataclass(frozen=True, slots=True)
class UnresolvedIdentifier:
    provider: str
    provider_id: str
    observation_date: date


@dataclass(frozen=True, slots=True)
class AmbiguousIdentifier:
    matches: tuple[tuple[str, date, date], ...]


class IdentityRegistry:
    """In-memory effective-date domain registry used by the application layer."""

    def __init__(self) -> None:
        self._identities: dict[str, list[IdentityVersion]] = {}
        self._mappings: dict[str, list[IdentifierMapping]] = {}

    def register(self, version: IdentityVersion) -> None:
        identity = version.identity
        canonical = self._canonical_id(identity.market, identity.instrument_type, identity.local_code)
        derived = version if version.canonical_security_id == canonical else IdentityVersion(
            version_id=_version_id(canonical, identity.valid_from),
            canonical_security_id=canonical,
            identity=identity,
            name=version.name,
            listing_date=version.listing_date,
            status=version.status,
            currency=version.currency,
            termination_date=version.termination_date,
        )
        self._ensure_no_overlap(
            self._identities.setdefault(canonical, []),
            derived.identity.valid_from,
            derived.identity.valid_to,
        )
        self._identities[canonical].append(derived)

    def register_mapping(self, mapping: IdentifierMapping) -> None:
        mapping_id = mapping.mapping_id
        expected = _mapping_id(
            mapping.provider,
            mapping.provider_id,
            mapping.valid_from,
        )
        if mapping_id and mapping_id != expected:
            raise ValueError("mapping id is not canonical")
        self._ensure_no_overlap(
            self._mappings.setdefault(f"{mapping.provider}:{mapping.provider_id}", []),
            mapping.valid_from,
            mapping.valid_to,
        )
        self._mappings[f"{mapping.provider}:{mapping.provider_id}"].append(mapping)

    def resolve(
        self,
        provider: str,
        provider_id: str,
        observation_date: date,
    ) -> Result[ResolvedIdentifier, UnresolvedIdentifier | AmbiguousIdentifier]:
        matches = tuple(
            mapping
            for mapping in self._mappings.get(_mapping_key(provider, provider_id), ())
            if mapping.valid_from <= observation_date <= mapping.valid_to
        )
        if not matches:
            return Failure(UnresolvedIdentifier(provider, provider_id, observation_date))
        if len(matches) > 1:
            return Failure(
                AmbiguousIdentifier(tuple(
                    (mapping.canonical_security_id, mapping.valid_from, mapping.valid_to)
                    for mapping in matches
                ))
            )
        return Success(ResolvedIdentifier(matches[0].canonical_security_id))

    def identity_history(self, canonical_security_id: str) -> tuple[IdentityVersion, ...]:
        return tuple(self._identities.get(canonical_security_id, ()))

    def mapping_history(
        self,
        provider: str,
        provider_id: str,
    ) -> tuple[IdentifierMapping, ...]:
        return tuple(self._mappings.get(_mapping_key(provider, provider_id), ()))

    @staticmethod
    def _ensure_no_overlap(
        versions: Sequence[IdentityVersion | IdentifierMapping],
        valid_from: date,
        valid_to: date | None,
    ) -> None:
        version_from = valid_from
        version_to = valid_to if valid_to is not None else date.max
        for history in versions:
            history_to = history.valid_to
            if history_to is None:
                history_to = date.max
            if version_from <= history_to and history.valid_from <= version_to:
                raise ValueError("effective versions overlap")

    @staticmethod
    def _canonical_id(market: str, instrument_type: str, local_code: str) -> str:
        key = f"{market}:{instrument_type}:{local_code}"
        return f"urn:stock-research:{market}:{instrument_type}:{uuid5(NAMESPACE_URL, key).hex}"


def _version_id(canonical_id: str, valid_from: date) -> str:
    return uuid5(NAMESPACE_URL, f"{canonical_id}:{valid_from}").hex


def _mapping_key(provider: str, provider_id: str) -> str:
    return f"{provider}:{provider_id}"


def _mapping_id(provider: str, provider_id: str, valid_from: date) -> str:
    return uuid5(NAMESPACE_URL, f"{provider}:{provider_id}:{valid_from}").hex
