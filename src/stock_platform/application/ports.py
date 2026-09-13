from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class CredentialStore(Protocol):
    """The minimal application port for credential reads and deletions."""

    def get(self, provider: str, reference: str) -> str | None: ...

    def delete(self, provider: str, reference: str) -> None: ...


@runtime_checkable
class DatasetPublisher(Protocol):
    """The minimal application port for immutable dataset publication."""

    def publish(
        self,
        schema: object,
        rows: tuple[dict[str, object], ...],
        *,
        dataset_name: str,
    ) -> Path: ...
