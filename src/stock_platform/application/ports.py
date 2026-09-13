from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CredentialStore(Protocol):
    """The minimal application port for credential reads and deletions."""

    def get(self, provider: str, reference: str) -> str | None: ...

    def delete(self, provider: str, reference: str) -> None: ...
