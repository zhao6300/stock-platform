from __future__ import annotations

from hashlib import sha256

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.application.errors import ErrorCode
from stock_platform.application.policy import MvpPolicy, UnsupportedCapability
from stock_platform.domain.common import Failure, Success


@given(requested=st.sets(st.sampled_from(UnsupportedCapability)))
def test_all_unsupported_capability_subsets_are_inert(
    requested: set[UnsupportedCapability],
) -> None:
    persisted_observation = {"value": "unchanged"}
    before = sha256(repr(persisted_observation).encode()).hexdigest()

    result = MvpPolicy.validate(requested)

    after = sha256(repr(persisted_observation).encode()).hexdigest()
    assert before == after
    if requested:
        assert isinstance(result, Failure)
        assert result.error.code == ErrorCode.UNSUPPORTED_CAPABILITY
        assert set(result.error.context["unsupported"]) == {item.value for item in requested}
    else:
        assert isinstance(result, Success)
