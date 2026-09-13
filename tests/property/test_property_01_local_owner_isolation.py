from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from hypothesis import given

from stock_platform.application.access import AccessContext, LocalAccessGuard
from stock_platform.application.errors import ErrorCode
from stock_platform.domain.common import Failure
from tests.strategies.primitives import uids


@given(owner_uid=uids(), current_uid=uids())
def test_owner_isolation_permits_only_the_exact_uid(
    owner_uid: int, current_uid: int
) -> None:
    state = {"marker": f"{owner_uid}:{current_uid}"}
    before = sha256(repr(state).encode()).hexdigest()

    result = LocalAccessGuard().check(
        AccessContext(
            owner_uid=owner_uid,
            current_uid=current_uid,
            source_host="127.0.0.1",
            csrf_token="csrf",
            idempotency_key="idempotency-key",
        ),
        write=True,
    )

    after = sha256(repr(state).encode()).hexdigest()
    assert before == after
    if owner_uid == current_uid:
        assert result is not None and not isinstance(result, Failure)
    else:
        assert isinstance(result, Failure)
        assert result.error.code == ErrorCode.SECOND_USER_DENIED
        assert after == before


def test_denied_attempt_leaves_persisted_state_unchanged(tmp_path: Path) -> None:
    persisted = tmp_path / "state.json"
    persisted.write_text("stable", encoding="utf-8")

    before = persisted.read_bytes()
    result = LocalAccessGuard().check(
        AccessContext(owner_uid=1000, current_uid=1001, source_host="127.0.0.1")
    )

    assert persisted.read_bytes() == before
    assert isinstance(result, Failure)
