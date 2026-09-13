from __future__ import annotations

from stock_platform.application.access import (
    AccessContext,
    LocalAccessGuard,
    require_local_access,
)
from stock_platform.application.errors import ErrorCode
from stock_platform.domain.common import Failure, Success


def test_guard_allows_the_exact_local_owner_for_read_sessions() -> None:
    result = LocalAccessGuard().check(
        AccessContext(owner_uid=1000, current_uid=1000, source_host="127.0.0.1")
    )

    assert isinstance(result, Success)


def test_guard_rejects_distinct_effective_uid_before_write_markers() -> None:
    denied_value = LocalAccessGuard().check(
        AccessContext(owner_uid=1000, current_uid=1001, source_host="127.0.0.1")
    )
    denied_require = None
    try:
        require_local_access(
            AccessContext(owner_uid=1000, current_uid=1001, source_host="127.0.0.1"),
            write=True,
        )
    except Exception as error:
        denied_require = error

    assert isinstance(denied_value, Failure)
    assert denied_value.error.code == ErrorCode.SECOND_USER_DENIED
    assert denied_require is not None
    assert denied_require.envelope.code == ErrorCode.SECOND_USER_DENIED


def test_write_commands_require_loopback_csrf_and_idempotency() -> None:
    missing_csrf = LocalAccessGuard().check(
        AccessContext(owner_uid=1000, current_uid=1000, source_host="127.0.0.1"),
        write=True,
    )
    missing_key = LocalAccessGuard().check(
        AccessContext(
            owner_uid=1000,
            current_uid=1000,
            source_host="127.0.0.1",
            csrf_token="csrf",
        ),
        write=True,
    )
    non_loopback = LocalAccessGuard().check(
        AccessContext(owner_uid=1000, current_uid=1000, source_host="example.com")
    )

    assert missing_csrf.error.code == ErrorCode.VALIDATION_FAILED
    assert missing_key.error.code == ErrorCode.VALIDATION_FAILED
    assert non_loopback.error.code == ErrorCode.CONFIGURED_ENDPOINT_REQUIRED
