from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from stock_platform.domain.common import (
    JsonValue,
    canonical_value,
    ensure_timezone_aware,
)


class ErrorCode(StrEnum):
    """Stable public error codes used by the application boundary."""

    SECOND_USER_DENIED = "SECOND_USER_DENIED"
    CONFIGURED_ENDPOINT_REQUIRED = "CONFIGURED_ENDPOINT_REQUIRED"
    UNSUPPORTED_CAPABILITY = "UNSUPPORTED_CAPABILITY"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    CONFLICT = "CONFLICT"
    PROVIDER_RATE_LIMITED = "PROVIDER_RATE_LIMITED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    CREDENTIAL_UNAVAILABLE = "CREDENTIAL_UNAVAILABLE"
    INTERNAL = "INTERNAL"


type ErrorContext = dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class ErrorEnvelope:
    """A stable, serializable boundary error with deliberately safe context."""

    code: ErrorCode
    message: str
    context: Mapping[str, JsonValue]
    timestamp: datetime

    def __post_init__(self) -> None:
        ensure_timezone_aware(self.timestamp)
        if not self.message:
            raise ValueError("error message must not be empty")
        if not all(self.context):
            raise ValueError("error context keys must not be empty")

    @classmethod
    def build(
        cls,
        code: ErrorCode,
        message: str,
        context: Mapping[str, JsonValue] | None = None,
        *,
        timestamp: datetime | None = None,
    ) -> ErrorEnvelope:
        return cls(
            code=code,
            message=message,
            context=dict(cls._safe_values(context or {})),
            timestamp=timestamp or datetime.now(UTC),
        )

    @classmethod
    def _safe_values(cls, context: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
        return {str(key): canonical_value(value) for key, value in context.items()}


class ApplicationError(Exception):
    """Application-level exception carrying a stable ErrorEnvelope."""

    envelope: ErrorEnvelope

    def __init__(self, envelope: ErrorEnvelope) -> None:
        self.envelope = envelope
        super().__init__(envelope.message)


class CredentialUnavailableError(ApplicationError):
    """Used when Keychain cannot provide the requested credential."""


def credential_unavailable(provider: str, reference: str) -> ApplicationError:
    """Return a stable provider/context error without credential material."""
    return ApplicationError(
        ErrorEnvelope.build(
            code=ErrorCode.CREDENTIAL_UNAVAILABLE,
            message="credential unavailable for provider",
            context={"provider": provider, "credential_reference": reference},
        )
    )
