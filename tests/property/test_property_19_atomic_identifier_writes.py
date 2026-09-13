from __future__ import annotations

from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st
from sqlalchemy import select

from stock_platform.domain.identifiers import IdentityKey, IdentityVersion
from stock_platform.infrastructure.sqlite.models import SecurityIdentity
from stock_platform.infrastructure.sqlite.repository import SQLiteSecurityRepository
from stock_platform.infrastructure.sqlite.unit_of_work import SQLiteUnitOfWork


@given(
    initial_status=st.sampled_from(("ACTIVE", "SUSPENDED", "TERMINATED")),
    duplicate_status=st.sampled_from(("ACTIVE", "SUSPENDED", "TERMINATED")),
)
def test_transaction_rolls_back_duplicate_batches(
    initial_status: str, duplicate_status: str
) -> None:
    unit_of_work = SQLiteUnitOfWork("sqlite:///:memory:")
    identity = IdentityKey(
        market="CN",
        instrument_type="A_Share",
        local_code="600000",
        valid_from=date(2025, 1, 1),
    )
    duplicate = IdentityVersion(
        version_id="identity-1",
        canonical_security_id=f"{initial_status}:{duplicate_status}",
        identity=identity,
        name="Name",
        listing_date=date(2025, 1, 1),
        status=initial_status,
        currency="CNY",
        termination_date=None,
    )
    with pytest.raises(ValueError), unit_of_work.begin() as session:
        repository = SQLiteSecurityRepository(session)
        repository.register_identity(duplicate)
        repository.register_identity(duplicate)
    with unit_of_work.begin() as session:
        assert session.scalars(select(SecurityIdentity)).first() is None
