from __future__ import annotations

import pytest

from stock_platform.domain.common import Failure, Success
from stock_platform.domain.instruments import (
    ClassifiedInstrument,
    InstrumentClassifier,
)


@pytest.mark.parametrize(
    ("instrument_type", "market"),
    [("A_SHARE", "CN"), ("HK_EQUITY", "HK"), ("ETF", "CN"), ("OPEN_END_FUND", "FUND")],
)
def test_supported_instruments_classify_without_ambiguity(
    instrument_type: str, market: str
) -> None:
    result = InstrumentClassifier().classify(instrument_type)  # type: ignore[arg-type]

    assert result == Success(ClassifiedInstrument(instrument_type, market))


def test_unsupported_instrument_type_is_rejected() -> None:
    result = InstrumentClassifier().classify("OTHER")

    assert isinstance(result, Failure)
