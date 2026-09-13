from __future__ import annotations

from dataclasses import dataclass, field

from stock_platform.application.credentials import (
    CredentialSelection,
    delete_credential_selection,
)
from stock_platform.domain.common import Success


@dataclass
class FakeKeychain:
    secrets: dict[str, str] = field(default_factory=dict)

    def get(self, provider: str, reference: str) -> str | None:
        return self.secrets.get(f"{provider}/{reference}")

    def set(self, provider: str, reference: str, secret: str) -> None:
        self.secrets[f"{provider}/{reference}"] = secret

    def delete(self, provider: str, reference: str) -> None:
        self.secrets.pop(f"{provider}/{reference}", None)


def test_exact_selection_deletes_only_selected_credentials() -> None:
    store = FakeKeychain()
    store.set("alpha", "delete_me", "secret-a")
    store.set("alpha", "keep_me", "secret-b")

    result = delete_credential_selection(
        store,
        "alpha",
        ["delete_me"],
        remaining=["delete_me", "keep_me"],
    )

    assert result == Success(CredentialSelection(selected=("delete_me",), remaining=("keep_me",)))
