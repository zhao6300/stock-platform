from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.common import Failure, Success
from stock_platform.domain.instruments import (
    _MARKET_BY_TYPE,
    _SUPPORTED_TYPES,
    InstrumentClassifier,
    SupportedType,
)


@given(value=st.sampled_from(_SUPPORTED_TYPES))
def test_exactly_one_classification_is_assigned(value: SupportedType) -> None:
    result = InstrumentClassifier().classify(value)
    assert isinstance(result, Success)
    assert result.value.instrument_type in _MARKET_BY_TYPE


@given(value=st.text())
def test_unsupported_classification_is_rejected(value: str) -> None:
    if value in _SUPPORTED_TYPES:
        assert InstrumentClassifier().classify(value) is not None
        return
    assert isinstance(InstrumentClassifier().classify(value), Failure)
