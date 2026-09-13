from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from stock_platform.application.ports import CredentialStore
from stock_platform.domain.common import Failure, Result, Success


@dataclass(frozen=True, slots=True)
class CredentialSelection:
    """Exact selected/remaining credential references after deletion."""

    selected: tuple[str, ...]
    remaining: tuple[str, ...]


def _flat_references(selected: Sequence[str]) -> tuple[str, ...]:
    """Return references; if item is a string, reject and return empty tuple."""
    if isinstance(selected, str):
        return ()
    return tuple(selected)


def delete_credential_selection(
    store: CredentialStore,
    provider: str,
    selected: Sequence[str],
    remaining: Sequence[str] = (),
) -> Result[CredentialSelection, str]:
    """Delete exactly selected references and preserve every other one."""
    if not provider:
        return Failure("credential provider must not be blank")
    references = _flat_references(selected)
    if any(not reference for reference in references):
        return Failure("selected credential references must not be blank")
    if len(set(references)) != len(references):
        return Failure("selected credential references must be unique")
    for reference in references:
        store.delete(provider, reference)
    return Success(
        CredentialSelection(
            selected=references,
            remaining=tuple(
                reference
                for reference in _flat_references(remaining)
                if not references or reference not in references
            ),
        )
    )
