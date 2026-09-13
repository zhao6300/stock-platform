from __future__ import annotations

from dataclasses import dataclass, field

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.application.credentials import (
    CredentialSelection,
    delete_credential_selection,
)


@dataclass
class FakeKeychain:
    deleted: tuple[str, ...] = ()
    secrets: dict[str, str] = field(default_factory=dict)

    def get(self, provider: str, reference: str) -> str | None:
        return self.secrets.get(f"{provider}/{reference}")

    def delete(self, provider: str, reference: str) -> None:
        if not provider or not reference:
            raise ValueError("credential references must be non-empty")
        self.deleted = (*self.deleted, f"{provider}/{reference}")
        self.secrets.pop(f"{provider}/{reference}", None)


def unique_without_duplicates(values: list[str]) -> bool:
    return len(set(values)) == len(values)


@given(
    provider=st.from_regex(r"\w+", fullmatch=True),
    selected=st.lists(st.from_regex(r"\w+", fullmatch=True), max_size=5).filter(
        unique_without_duplicates
    ),
    kept=st.lists(st.from_regex(r"\w+", fullmatch=True), max_size=5).filter(
        unique_without_duplicates
    ),
)
def test_selected_credentials_are_deleted_exactly_and_kept_references_remain(
    provider: str,
    selected: list[str],
    kept: list[str],
) -> None:
    kept = [reference for reference in kept if reference not in selected]
    provider = "default-provider"
    selected = selected or ["default-selection"]
    remaining = tuple(kept or [f"{provider}-kept-first"])
    store = FakeKeychain(
        secrets={
            f"{provider}/{reference}": f"secret-{reference}"
            for reference in (*selected, *remaining)
        }
    )

    result = delete_credential_selection(
        store,
        provider,
        selected,
        remaining=kept or [f"{provider}-kept-first"],
    )

    assert result is not None
    assert result.value == CredentialSelection(tuple(selected), tuple(remaining))
    assert len(store.deleted) == len(selected)
    assert set(store.deleted) == {f"{provider}/{reference}" for reference in selected}
    assert all(f"{provider}/{reference}" in store.secrets for reference in remaining)
