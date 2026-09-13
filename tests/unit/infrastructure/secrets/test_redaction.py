from __future__ import annotations

from stock_platform.infrastructure.secrets.redaction import redact


def test_secret_redacts_known_variants() -> None:
    value = {
        "authorization": "Bearer token",
        "nested": {"url": "?password=token"},
        "bytes": b"token",
    }
    result = redact(value, b"token")

    assert result["authorization"] == "Bearer [REDACTED]"
    assert result["nested"]["url"] == "?password=[REDACTED]"
    assert result["bytes"] == b"[REDACTED]"
