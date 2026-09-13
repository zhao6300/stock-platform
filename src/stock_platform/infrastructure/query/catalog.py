from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from stock_platform.infrastructure.query.service import (
    MarketInstrumentPair,
)


class ParquetCatalog:
    """Path-backed readonly catalog for pinned market data files."""

    def __init__(self, paths: Mapping[MarketInstrumentPair, Path]) -> None:
        self._paths = dict(paths)

    def open(self, market: str, instrument_type: str) -> Path:
        return self._paths[(market, instrument_type)]

    def markets(self, instrument_type: str) -> tuple[str, ...]:
        return tuple(market for market, kind in self._paths if kind == instrument_type)
