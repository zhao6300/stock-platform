from __future__ import annotations

from typing import Protocol

_SERVICE = "stock-research"


class KeychainBackend(Protocol):
    def get_password(self, service: str, reference: str) -> str | None: ...
    def set_password(self, service: str, reference: str, secret: str) -> None: ...
    def delete_password(self, service: str, reference: str) -> None: ...


class KeychainStore:
    """Minimal-scope credential writes and reads through Keychain only."""

    def __init__(self, backend: KeychainBackend | None = None, namespace: str = _SERVICE) -> None:
        self._backend = backend
        self._namespace = namespace

    def service(self, provider: str) -> str:
        return f"{self._namespace}/{provider}"

    def reference(self, reference: str) -> str:
        return reference

    def set(self, provider: str, reference: str, secret: str) -> str:
        """Store one credential reference and return the safe reference."""
        if not provider:
            raise ValueError("credential provider must be non-empty")
        if not reference:
            raise ValueError("credential reference must be non-empty")
        self._load().set_password(self.service(provider), self.reference(reference), secret)
        return self.reference(reference)

    def get(self, provider: str, reference: str) -> str | None:
        """Read one credential only when the caller needs it."""
        return self._load().get_password(self.service(provider), self.reference(reference))

    def delete(self, provider: str, reference: str) -> None:
        """Delete exactly one Keychain-hosted credential."""
        self._load().delete_password(self.service(provider), self.reference(reference))

    def _load(self) -> KeychainBackend:
        if self._backend is not None:
            return self._backend

        return _KeyringAdapter()


class _KeyringAdapter:
    def get_password(self, service: str, reference: str) -> str | None:
        import keyring

        return keyring.get_password(service, reference)

    def set_password(self, service: str, reference: str, secret: str) -> None:
        import keyring

        keyring.set_password(service, reference, secret)

    def delete_password(self, service: str, reference: str) -> None:
        import keyring

        keyring.delete_password(service, reference)
