from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from stock_platform.application.errors import ErrorCode, ErrorEnvelope
from stock_platform.domain.common import Failure, Result, Success

type LocalHost = Literal["127.0.0.1", "::1"]


@dataclass(frozen=True, slots=True)
class AccessContext:
    """Input facts captured at the application boundary before side effects."""

    owner_uid: int
    current_uid: int
    source_host: str
    csrf_token: str | None = None
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class AllowedAccess:
    csrf_token: str | None
    idempotency_key: str | None


def _denied_detected() -> Failure[ErrorEnvelope]:
    return Failure(
        ErrorEnvelope.build(
            ErrorCode.SECOND_USER_DENIED,
            "This MVP permits exactly one local user.",
        )
    )


class LocalAccessGuard:
    """Reject a second effective user before any transaction or service work."""

    def check(
        self, context: AccessContext, *, write: bool = False
    ) -> Result[AllowedAccess, ErrorEnvelope]:
        if context.owner_uid != context.current_uid:
            return _denied_detected()
        if context.source_host not in ("127.0.0.1", "::1"):
            return Failure(
                ErrorEnvelope.build(
                    ErrorCode.CONFIGURED_ENDPOINT_REQUIRED,
                    "Only loopback hosts may access the local platform.",
                )
            )
        if write:
            if not context.csrf_token:
                return Failure(
                    ErrorEnvelope.build(
                        ErrorCode.VALIDATION_FAILED, "A CSRF token is required."
                    )
                )
            if not context.idempotency_key:
                return Failure(
                    ErrorEnvelope.build(
                        ErrorCode.VALIDATION_FAILED, "An idempotency key is required."
                    )
                )
        return Success(
            AllowedAccess(
                csrf_token=context.csrf_token,
                idempotency_key=context.idempotency_key,
            )
        )


def require_local_access(
    context: AccessContext, *, write: bool = False
) -> AllowedAccess:
    """Validate access and raise prior to transactions or provider network calls."""

    result = LocalAccessGuard().check(context, write=write)
    if isinstance(result, Failure):
        raise ApplicationAccessError(result.error)
    return result.value


class ApplicationAccessError(Exception):
    """Raised after the access guard has returned a typed denial."""

    def __init__(self, envelope: ErrorEnvelope) -> None:
        self.envelope = envelope
        super().__init__(envelope.message)
