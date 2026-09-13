from __future__ import annotations

from datetime import date

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.identifiers import IdentityKey, IdentityVersion


@given(status=st.sampled_from(("ACTIVE", "SUSPENDED", "TERMINATED")))
def test_history_persists_multiple_versions(status: str) -> None:
    history: list[IdentityVersion] = []
    for month in (1, 2):
        history.append(
            IdentityVersion(
                "identity-1",
                "canonical",
                IdentityKey("CN", "A_Share", "600000", date(2025, month, 1)),
                "Name",
                date(2025, month, 1),
                status,
                "CNY",
                None,
            )
        )

    assert [version.identity.valid_from for version in history] == [
        date(2025, 1, 1),
        date(2025, 2, 1),
    ]
