from __future__ import annotations

from base64 import b64encode, urlsafe_b64encode
from urllib.parse import quote

from stock_platform.infrastructure.secrets.redaction import redact


def encoded_variants(secret: str) -> tuple[str, ...]:
    raw = secret.encode("utf-8")
    base64 = b64encode(raw).decode("ascii")
    urlsafe_base64 = urlsafe_b64encode(raw).decode("ascii")
    return (
        secret,
        base64,
        urlsafe_base64,
        quote(secret, safe=""),
        quote(base64, safe=""),
        quote(urlsafe_base64, safe=""),
    )


def test_secret_variants_never_reach_a_persisted_sink() -> None:
    secret = "SECRET_60"
    variants = encoded_variants(secret)
    redacted = redact(variants, secret)

    assert secret not in repr(redacted)
