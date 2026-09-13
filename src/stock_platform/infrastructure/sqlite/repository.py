from __future__ import annotations

from datetime import date
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from stock_platform.domain.calendars import CalendarVersion
from stock_platform.domain.common import Failure, Result, Success
from stock_platform.domain.identifiers import (
    AmbiguousIdentifier,
    IdentifierMapping,
    IdentityVersion,
    ResolvedIdentifier,
    UnresolvedIdentifier,
)
from stock_platform.infrastructure.sqlite.models import (
    CalendarDay,
    Provider,
    SecurityMappingVersion,
    SecurityMasterVersion,
)
from stock_platform.infrastructure.sqlite.models import (
    CalendarVersion as CalendarVersionRow,
)
from stock_platform.infrastructure.sqlite.models import (
    SecurityIdentity as SecurityIdentityRow,
)


class SQLiteSecurityRepository:
    """Effective-dated identifier storage with explicit insert-only operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def register_identity(self, version: IdentityVersion) -> None:
        identity = version.identity
        canonical_security_id = _canonical_security_id(
            identity.market,
            identity.instrument_type,
            identity.local_code,
        )
        security = self._identity(canonical_security_id)
        if security is None:
            security = SecurityIdentityRow(
                canonical_security_id=canonical_security_id,
                market=identity.market,
                instrument_type=identity.instrument_type,
                local_code=identity.local_code,
                created_at=date.today(),
            )
            self._session.add(security)
            self._session.flush()

        if self._identity_overlaps(security.id, identity.valid_from, identity.valid_to):
            raise ValueError("identity versions overlap")
        self._session.add(
            SecurityMasterVersion(
                version_id=version.version_id,
                security_id=security.id,
                name=version.name,
                currency=version.currency,
                listing_date=version.listing_date,
                termination_date=version.termination_date,
                status=version.status,
                valid_from=identity.valid_from,
                valid_to=identity.valid_to,
                created_at=date.today(),
            )
        )
        self._session.flush()

    def register_mapping(self, mapping: IdentifierMapping) -> None:
        identity = self._identity(mapping.canonical_security_id)
        if identity is None:
            raise LookupError(f"canonical identity not found: {mapping.canonical_security_id}")
        provider_id = _provider_id(self._session, mapping.provider)
        if self._mapping_overlaps(
            provider_id, mapping.provider_id, mapping.valid_from, mapping.valid_to
        ):
            raise ValueError("mapping versions overlap")
        self._session.add(
            SecurityMappingVersion(
                version_id=mapping.mapping_id or _mapping_version_id(mapping),
                provider_id=provider_id,
                provider_identifier=mapping.provider_id,
                security_id=identity.id,
                valid_from=mapping.valid_from,
                valid_to=mapping.valid_to,
                created_at=date.today(),
            )
        )
        self._session.flush()

    def resolve(
        self,
        provider_name: str,
        provider_identifier: str,
        observation_date: date,
    ) -> Result[ResolvedIdentifier, UnresolvedIdentifier | AmbiguousIdentifier]:
        provider = self._session.scalar(select(Provider).where(Provider.name == provider_name))
        if provider is None:
            return Failure(
                UnresolvedIdentifier(provider_name, provider_identifier, observation_date)
            )
        matches = list(
            self._session.scalars(
                select(SecurityMappingVersion).where(
                    SecurityMappingVersion.provider_id == provider.id,
                    SecurityMappingVersion.provider_identifier == provider_identifier,
                    SecurityMappingVersion.valid_from <= observation_date,
                    SecurityMappingVersion.valid_to >= observation_date,
                )
            )
        )
        if not matches:
            return Failure(
                UnresolvedIdentifier(provider_name, provider_identifier, observation_date)
            )
        if len(matches) > 1:
            return Failure(
                AmbiguousIdentifier(
                    tuple(
                        (
                            self._lookup_canonical(match.security_id),
                            match.valid_from,
                            match.valid_to,
                        )
                        for match in matches
                    )
                )
            )
        security = self._session.get(SecurityIdentityRow, matches[0].security_id)
        if security is None:
            raise LookupError(f"canonical identity not found: {matches[0].security_id}")
        canonical_security_id = security.canonical_security_id
        return Success(ResolvedIdentifier(canonical_security_id))

    def _lookup_canonical(self, security_id: int) -> str:
        security = self._session.get(SecurityIdentityRow, security_id)
        if security is None:
            raise LookupError(f"canonical identity not found: {security_id}")
        return security.canonical_security_id

    def _identity(self, canonical_security_id: str) -> SecurityIdentityRow | None:
        return self._session.scalar(
            select(SecurityIdentityRow).where(
                SecurityIdentityRow.canonical_security_id == canonical_security_id
            )
        )

    def _identity_overlaps(self, security_id: int, valid_from: date, valid_to: date | None) -> bool:
        target_to = valid_to or date.max
        return any(
            valid_from <= (row.valid_to or date.max) and row.valid_from <= target_to
            for row in self._session.scalars(
                select(SecurityMasterVersion).where(
                    SecurityMasterVersion.security_id == security_id
                )
            )
        )

    def _mapping_overlaps(
        self,
        provider_id: int,
        provider_identifier: str,
        valid_from: date,
        valid_to: date,
    ) -> bool:
        return any(
            valid_from <= existing.valid_to and existing.valid_from <= valid_to
            for existing in self._session.scalars(
                select(SecurityMappingVersion).where(
                    SecurityMappingVersion.provider_id == provider_id,
                    SecurityMappingVersion.provider_identifier == provider_identifier,
                )
            )
        )


class SQLiteCalendarRepository:
    """Store exact calendar versions and their member dates."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def register(self, version: CalendarVersion) -> None:
        calendar = CalendarVersionRow(
            version_id=version.version_id,
            calendar_type=version.kind,
            market=version.market,
            timezone_name=version.timezone,
            valid_from=version.valid_from,
            valid_to=version.valid_to,
            created_at=date.today(),
        )
        self._session.add(calendar)
        self._session.flush()
        for calendar_date in version.open_dates or version.expected_dates or frozenset():
            self._session.add(
                CalendarDay(
                    calendar_id=calendar.id,
                    observation_date=calendar_date,
                    open=version.kind == "TRADING",
                    session="REGULAR",
                    tradability="OPEN",
                )
            )
        self._session.flush()


def _provider_id(session: Session, provider_name: str) -> int:
    provider = session.scalar(select(Provider).where(Provider.name == provider_name))
    if provider is not None:
        return provider.id
    provider = Provider(name=provider_name, created_at=date.today())
    session.add(provider)
    session.flush()
    return provider.id


def _canonical_security_id(market: str, instrument_type: str, local_code: str) -> str:
    value = f"{market}:{instrument_type}:{local_code}"
    return f"urn:stock-research:{market}:{instrument_type}:{uuid5(NAMESPACE_URL, value).hex}"


def _mapping_version_id(mapping: IdentifierMapping) -> str:
    key = f"{mapping.provider}:{mapping.provider_id}:{mapping.valid_from.isoformat()}"
    return uuid5(NAMESPACE_URL, key).hex
