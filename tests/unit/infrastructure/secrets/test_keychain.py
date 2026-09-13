from __future__ import annotations

from dataclasses import dataclass, field

from stock_platform.infrastructure.secrets.keychain import KeychainStore


@dataclass
class FakeKeychain:
    secrets: dict[str, str] = field(default_factory=dict)

    def get_password(self, service: str, reference: str) -> str | None:
        return self.secrets.get(f"{service}/{reference}")

    def set_password(self, service: str, reference: str, secret: str) -> None:
        self.secrets[f"{service}/{reference}"] = secret

    def delete_password(self, service: str, reference: str) -> None:
        self.secrets.pop(f"{service}/{reference}", None)


def test_keychain_store_uses_provider_scoped_service_and_reference() -> None:
    adapter = FakeKeychain()
    store = KeychainStore(adapter)

    reference = store.set("alpha", "token:one", "secret-value")

    assert reference == "token:one"
    assert adapter.secrets == {"stock-research/alpha/token:one": "secret-value"}
    assert store.get("alpha", "token:one") == "secret-value"
    store.delete("alpha", "token:one")
    assert adapter.secrets == {}
