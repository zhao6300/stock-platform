from __future__ import annotations

from datetime import UTC, datetime

from hypothesis import given
from hypothesis.strategies import text

from stock_platform.application.errors import ErrorCode, ErrorEnvelope


@given(message=text(alphabet="42a", min_size=1, max_size=52))
def test_error_session_context(message: str) -> None:
    context = ErrorEnvelope.build(
        code=ErrorCode.INTERNAL,
        message=message,
        context={"session": "session-1"},
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert context.context == {"session": "session-1"}
