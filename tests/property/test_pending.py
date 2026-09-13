from __future__ import annotations

from stock_platform.domain.research import PendingKeyword


def test_pending_keyword_is_pending() -> None:
    value = PendingKeyword("1")
    assert value.pending == ("1",)
