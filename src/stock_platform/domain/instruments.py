from __future__ import annotations

from dataclasses import dataclass

from stock_platform.domain.common import (
    Failure,
    Result,
    Success,
)

type InstrumentType = str
type Market = str
type SupportedType = str

_MARKET_BY_TYPE = {
    "A_SHARE": "CN",
    "HK_EQUITY": "HK",
    "ETF": "CN",
    "OPEN_END_FUND": "FUND",
}
_SUPPORTED_TYPES = tuple(_MARKET_BY_TYPE)


@dataclass(frozen=True, slots=True)
class ClassifiedInstrument:
    instrument_type: InstrumentType
    market: Market


@dataclass(frozen=True, slots=True)
class ClassificationError:
    reason: str


type ClassificationResult = Result[ClassifiedInstrument, ClassificationError]


@dataclass(frozen=True, slots=True)
class InstrumentClassifier:
    def classify(self, instrument_type: InstrumentType) -> ClassificationResult:
        market = _MARKET_BY_TYPE.get(instrument_type)
        if market is None:
            return Failure(ClassificationError(instrument_type))
        return Success(ClassifiedInstrument(instrument_type, market))
