from __future__ import annotations

import pytest

from stock_platform.infrastructure.backup.encryption import (
    CredentialCapsule,
    create_credential_capsule,
    open_credential_capsule,
)


def test_credential_capsule_round_trips_password_derived_content() -> None:
    payload = b"secret-token"
    capsule = create_credential_capsule(payload, b"backup-password")

    assert isinstance(capsule, CredentialCapsule)
    assert capsule.salt != capsule.nonce
    assert capsule.ciphertext != payload
    assert open_credential_capsule(capsule, b"backup-password") == payload
    with pytest.raises(ValueError):
        open_credential_capsule(capsule, b"wrong-password")


def test_credential_capsule_rejects_empty_payload_and_password() -> None:
    with pytest.raises(ValueError):
        create_credential_capsule(b"", b"password")
    with pytest.raises(ValueError):
        create_credential_capsule(b"payload", b"")
