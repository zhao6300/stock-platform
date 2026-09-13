from __future__ import annotations

from stock_platform.domain.research import PendingKeyword


def test_pending_keyword_is_typed() -> None:
    keyword = PendingKeyword("1")
    assert keyword.pending == ("1",)
