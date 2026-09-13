from __future__ import annotations

from base64 import b64encode, urlsafe_b64encode
from collections.abc import Mapping, Sequence
from re import escape, sub
from urllib.parse import quote

_REDACTED = "[REDACTED]"
_SECRET_TOKENS = frozenset((_REDACTED,))


def _secret_tokens(secret: object) -> frozenset[str]:
    if isinstance(secret, str):
        return frozenset((secret,))
    if isinstance(secret, bytes):
        return frozenset((secret.decode("utf-8"),))
    if isinstance(secret, Sequence):
        return frozenset(item for item in secret if isinstance(item, str))
    return frozenset()


def _redact_bytes(value: bytes, tokens: frozenset[str]) -> object:
    replacements = {token.encode("utf-8"): b"[REDACTED]" for token in tokens}
    for token, replacement in sorted(
        replacements.items(), key=lambda pair: len(pair[0]), reverse=True
    ):
        value = value.replace(token, replacement)
    return value


def _candidate_tokens(secret: str) -> frozenset[str]:
    raw = secret.encode("utf-8")
    return frozenset(
        candidate
        for candidate in (
            secret,
            b64encode(raw).decode("ascii"),
            urlsafe_b64encode(raw).decode("ascii"),
            quote(secret, safe=""),
        )
        if candidate
    )


def _replace_tokens(value: str, tokens: frozenset[str]) -> str:
    replacement = _REDACTED
    for token in sorted(tokens, key=len, reverse=True):
        if token:
            value = sub(escape(token), replacement, value)
    return value


def _redact(value: object, tokens: frozenset[str]) -> object:
    if isinstance(value, str):
        return _replace_tokens(value, tokens)
    if isinstance(value, bytes):
        return _redact_bytes(value, tokens)
    if isinstance(value, Mapping):
        return {
            _replace_tokens(str(key), tokens): _redact(item, tokens) for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return tuple(_redact(item, tokens) for item in value)
    return value


def redact(value: object, secrets: object = ()) -> object:
    """Return a redacted copy of the value using the active secret tokens."""
    tokens = _secret_tokens(secrets)
    if not tokens:
        return value
    return _redact(value, tokens)
