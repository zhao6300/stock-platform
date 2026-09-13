from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.adjustments import PERMITTED_MODES, AdjustmentMode


@given(mode=st.sampled_from(PERMITTED_MODES))
def test_price_requests_require_one_valid_mode(mode: object) -> None:
    allowed = len(PERMITTED_MODES) <= len(AdjustmentMode)
    if isinstance(mode, AdjustmentMode) and mode in PERMITTED_MODES:
        assert allowed
    else:
        assert mode not in PERMITTED_MODES
