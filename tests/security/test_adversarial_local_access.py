from __future__ import annotations

from hypothesis import given
from hypothesis.strategies import sampled_from

from stock_platform.application.access import AccessContext, LocalAccessGuard
from stock_platform.application.errors import ErrorCode
from stock_platform.domain.common import Failure

_HOSTS = ("example.com", "192.168.1.20", "10.0.0.10")


@given(source_host=sampled_from(_HOSTS), write=sampled_from([True, False]))
def test_non_loopback_hosts_reject_without_transmitting(
    source_host: str, write: bool
) -> None:
    context = AccessContext(owner_uid=1000, current_uid=1000, source_host=source_host)
    result = LocalAccessGuard().check(context, write=write)

    assert isinstance(result, Failure)
    assert result.error.code == ErrorCode.CONFIGURED_ENDPOINT_REQUIRED
