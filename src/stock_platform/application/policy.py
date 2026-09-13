from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from stock_platform.application.errors import ErrorCode, ErrorEnvelope
from stock_platform.domain.common import (
    Failure,
    Result,
    Success,
)


class UnsupportedCapability(Enum):
    """Documented market-use capabilities that remain outside the MVP."""

    ADDITIONAL_MARKETS = "additional markets beyond A-share, HK equity, and local funds"
    MINUTE_DATA = "minute data"
    TICK_DATA = "tick and trade data"
    REALTIME_STREAMING = "real-time or streaming market data"
    BROKER_CONNECTION = "broker connection"
    LIVE_TRADING = "live trading"
    ORDER_MODIFICATION = "order creation, modification, cancellation, or execution"
    SHORT_SELLING = "short selling"
    LEVERAGE = "leverage"
    DERIVATIVE_POSITIONS = "derivative positions"
    PARAMETER_OPTIMIZATION = "parameter optimization"
    MACHINE_LEARNING_TRAINING = "machine-learning training"
    DISTRIBUTED_COMPUTING = "distributed computing"
    MULTI_USER = "multi-user operation"
    REMOTE_DEPLOYMENT = "remote deployment"
    PUBLIC_DATA_SERVICE = "public or third-party data service"


@dataclass(frozen=True, slots=True)
class AllowedCapabilities:
    periods: Literal["DAILY"] = "DAILY"
    direction: str = "LONG_ONLY"
    leverage: str = "NONE"
    market_interaction: str = "RESEARCH_ONLY"


class MvpPolicy:
    @staticmethod
    def validate(
        requested: set[UnsupportedCapability],
    ) -> Result[AllowedCapabilities, ErrorEnvelope]:
        if requested:
            return Failure(
                ErrorEnvelope.build(
                    ErrorCode.UNSUPPORTED_CAPABILITY,
                    "Requested capabilities are unavailable in this MVP.",
                    context={
                        "unsupported": [
                            item.value for item in sorted(requested, key=lambda item: item.value)
                        ]
                    },
                )
            )
        return Success(AllowedCapabilities())
