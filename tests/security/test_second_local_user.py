from __future__ import annotations

from stock_platform.application.access import AccessContext, LocalAccessGuard
from stock_platform.application.errors import ErrorCode
from stock_platform.domain.common import Failure


def test_second_local_user_is_denied_without_transmitting() -> None:
    result = LocalAccessGuard().check(
        AccessContext(owner_uid=1000, current_uid=1001, source_host="127.0.0.1")
    )

    assert isinstance(result, Failure)
    assert result.error.code == ErrorCode.SECOND_USER_DENIED
