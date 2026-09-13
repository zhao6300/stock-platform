from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.application.ingestion import (
    SupportedCoverage,
    unsupported_coverage,
)
from stock_platform.domain.common import Failure, Success


@given(
    market=st.sampled_from(("CN", "HK")),
    instrument_type=st.sampled_from(("A_Share", "HK_Equity", "ETF", "Open_End_Fund")),
)
def test_unsupported_coverage_is_exact(market: str, instrument_type: str) -> None:
    coverage = [(market, instrument_type)]

    supported = unsupported_coverage(market, instrument_type, coverage)
    unsupported = unsupported_coverage(market, instrument_type, [])

    assert isinstance(supported, Success)
    assert supported.value == SupportedCoverage(market=market, instrument_type=instrument_type)
    assert isinstance(unsupported, Failure)
    assert unsupported.error.market == market
    assert unsupported.error.instrument_type == instrument_type
