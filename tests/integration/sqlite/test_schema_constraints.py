from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import update
from sqlalchemy.exc import DBAPIError

from stock_platform.domain.identifiers import (
    IdentifierMapping,
    IdentityKey,
    IdentityVersion,
)
from stock_platform.infrastructure.sqlite.models import SecurityMasterVersion
from stock_platform.infrastructure.sqlite.repository import (
    SQLiteSecurityRepository,
    _canonical_security_id,
)
from stock_platform.infrastructure.sqlite.unit_of_work import SQLiteUnitOfWork


def _identity_version(version_id: str, valid_from: date) -> IdentityVersion:
    canonical = _canonical_security_id("CN", "A_Share", "600000")
    return IdentityVersion(
        version_id=version_id,
        canonical_security_id=canonical,
        identity=IdentityKey(
            market="CN",
            instrument_type="A_Share",
            local_code="600000",
            valid_from=valid_from,
        ),
        name="Test Security",
        listing_date=valid_from,
        status="ACTIVE",
        currency="CNY",
        termination_date=None,
    )


def test_sqlite_repositories_reject_overlap_and_violations(tmp_path) -> None:
    unit = SQLiteUnitOfWork(f"sqlite:///{tmp_path / 'control.sqlite3'}")
    canonical = _canonical_security_id("CN", "A_Share", "600000")

    with unit.begin() as session:
        repository = SQLiteSecurityRepository(session)
        repository.register_identity(_identity_version("identity-v1", date(2024, 1, 1)))
        repository.register_mapping(
            IdentifierMapping(
                provider="reference",
                provider_id="000000",
                canonical_security_id=canonical,
                valid_from=date(2024, 1, 1),
                valid_to=date(2024, 12, 31),
            )
        )

    with unit.begin() as session:
        repository = SQLiteSecurityRepository(session)
        result = repository.resolve("reference", "000000", date(2024, 3, 1))
        assert result is not None
        assert result.value.canonical_security_id == canonical

    with unit.begin() as session:
        repository = SQLiteSecurityRepository(session)
        with pytest.raises(ValueError, match="mapping versions overlap"):
            repository.register_mapping(
                IdentifierMapping(
                    provider="reference",
                    provider_id="000000",
                    canonical_security_id=canonical,
                    valid_from=date(2024, 12, 31),
                    valid_to=date(2025, 12, 31),
                )
            )

    document = (
        update(SecurityMasterVersion)
        .where(SecurityMasterVersion.version_id == "identity-v1")
        .values(name="Changed")
    )
    with unit.begin() as session, pytest.raises(DBAPIError):
        session.execute(document)
