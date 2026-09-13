from __future__ import annotations

import os
from dataclasses import dataclass
from hashlib import scrypt

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_SALT_SIZE = 32
_KEY_SIZE = 32
_SCRYPT_WORK_FACTOR = 1 << 14
_SCRYPT_BLOCK_SIZE = 8
_SCRYPT_PARALLELIZATION = 1
_NONCE_SIZE = 12
_CAPSULE_VERSION = "capsule-v1"


@dataclass(frozen=True, slots=True)
class CredentialCapsule:
    """One AES-256-GCM capsule with explicit verification evidence."""

    version: str
    salt: bytes
    nonce: bytes
    ciphertext: bytes


def _derive_key(password: bytes, salt: bytes) -> bytes:
    return scrypt(
        password,
        salt=salt,
        dklen=_KEY_SIZE,
        n=_SCRYPT_WORK_FACTOR,
        r=_SCRYPT_BLOCK_SIZE,
        p=_SCRYPT_PARALLELIZATION,
    )


def create_credential_capsule(payload: bytes, password: bytes) -> CredentialCapsule:
    """Encrypt a payload only after deriving a key from password and random salt."""
    if not payload:
        raise ValueError("payload must contain credential bytes")
    if not password:
        raise ValueError("password must be at least one byte")

    salt = os.urandom(_SALT_SIZE)
    nonce = os.urandom(_NONCE_SIZE)
    key = _derive_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, payload, None)
    return CredentialCapsule(
        version=_CAPSULE_VERSION,
        salt=salt,
        nonce=nonce,
        ciphertext=ciphertext,
    )


def open_credential_capsule(capsule: CredentialCapsule, password: bytes) -> bytes:
    """Verify capsule authenticity and decrypt with the derived key."""
    if capsule.version != _CAPSULE_VERSION:
        raise ValueError(f"unsupported capsule version: {capsule.version}")
    try:
        key = _derive_key(password, capsule.salt)
        return AESGCM(key).decrypt(capsule.nonce, capsule.ciphertext, None)
    except Exception as error:
        raise ValueError("capsule verification failed") from error
