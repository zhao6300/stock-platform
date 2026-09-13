from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Any, Literal, Protocol

from stock_platform.domain.common import Failure, Result, Success, canonical_value

type MissingDecimal = Decimal | None
type SignalDirection = Literal["BUY", "SELL"]
type MissingPricePolicy = Literal["UNAVAILABLE", "FIVE_SESSION_FALLBACK"]
type TradabilityStatus = Literal[
    "OPEN", "SUSPENDED", "PRICE_LIMITED", "TERMINATED", "UNKNOWN"
]
type DataQualityStatus = Literal["OK", "WARNING", "REJECTED", "UNKNOWN"]


@dataclass(frozen=True, slots=True)
class TradingCalendarVersion:
    version_id: str
    market: str
    open_dates: frozenset[date]

    def __post_init__(self) -> None:
        if not self.version_id or not self.market:
            raise ValueError("calendar identifiers must not be empty")
        if not self.open_dates:
            raise ValueError("trading calendar requires open dates")

    @property
    def dates(self) -> tuple[date, ...]:
        return tuple(sorted(self.open_dates))


@dataclass(frozen=True, slots=True)
class DailyBar:
    instrument: str
    trading_date: date
    close: Decimal
    quality_status: DataQualityStatus = "OK"


@dataclass(frozen=True, slots=True)
class Tradability:
    instrument: str
    trading_date: date
    status: TradabilityStatus


class Strategy(Protocol):
    api_version: str
    required_capabilities: frozenset[str]

    def on_day_close(self, context: DayContext) -> Sequence[Signal]: ...


@dataclass(frozen=True, slots=True)
class AsOfMarketView:
    bars: Sequence[DailyBar]
    as_of: date

    def current_bar(self, instrument: str) -> DailyBar | None:
        candidates = (
            bar
            for bar in self.bars
            if bar.instrument == instrument and bar.trading_date <= self.as_of
        )
        return max(candidates, key=lambda bar: bar.trading_date, default=None)


@dataclass(frozen=True, slots=True)
class DayContext:
    trading_date: date
    history: AsOfMarketView
    positions: Mapping[str, Decimal]
    cash: Decimal


@dataclass(frozen=True, slots=True)
class Signal:
    instrument: str
    direction: SignalDirection
    requested_quantity: Decimal


@dataclass(frozen=True, slots=True)
class PendingSignal:
    signal_date: date
    execution_date: date
    signal: Signal


@dataclass(frozen=True, slots=True)
class CostModel:
    commission_rate: Decimal
    tax_rate: Decimal
    slippage_bps: Decimal
    minimum_fee: Decimal
    currency: str
    currency_precision: int = 2
    currency_rounding: str = ROUND_HALF_EVEN
    price_precision: int = 4
    price_rounding: str = ROUND_HALF_EVEN

    def __post_init__(self) -> None:
        rates = (self.commission_rate, self.tax_rate, self.slippage_bps, self.minimum_fee)
        if not self.currency or any(value < Decimal(0) for value in rates):
            raise ValueError("cost model values must be non-negative")
        if self.currency_precision < 0 or self.price_precision < 0:
            raise ValueError("rounding precision must not be negative")


@dataclass(frozen=True, slots=True)
class BacktestDisclosure:
    data_start: date
    data_end: date
    universe: frozenset[str]
    benchmark: str
    calendar_version: str
    adjustment_mode: str
    cost_model: CostModel
    missing_price_policy: MissingPricePolicy

    def as_dict(self) -> dict[str, object]:
        return {
            "data_start": canonical_value(self.data_start),
            "data_end": canonical_value(self.data_end),
            "universe": sorted(self.universe),
            "benchmark": self.benchmark,
            "calendar_version": self.calendar_version,
            "adjustment_mode": self.adjustment_mode,
            "cost_model": canonical_value(self.cost_model.__dict__),
            "missing_price_policy": self.missing_price_policy,
        }


@dataclass(frozen=True, slots=True)
class UnsupportedMVP:
    capabilities: frozenset[str]


@dataclass(frozen=True, slots=True)
class InvalidRequest:
    reason: str


@dataclass(frozen=True, slots=True)
class TradeRecord:
    trading_date: date
    instrument: str
    direction: SignalDirection
    requested_quantity: Decimal
    filled_quantity: Decimal
    reason: str
    execution_price: Decimal | None
    gross_value: Decimal | None
    cost_components: Mapping[str, Decimal]
    total_cost: Decimal
    net_cash_change: Decimal
    cash_delta: Decimal
    position_delta: Decimal


@dataclass(frozen=True, slots=True)
class ValuationRecord:
    trading_date: date
    instrument: str
    close: MissingDecimal
    source_date: date | None
    valuation_available: bool
    value: MissingDecimal


@dataclass(frozen=True, slots=True)
class PerformanceRecord:
    trading_date: date
    available: bool
    portfolio_value: MissingDecimal
    simple_return: MissingDecimal
    drawdown: MissingDecimal


@dataclass(frozen=True, slots=True)
class BacktestReport:
    disclosure: BacktestDisclosure
    signal_generation: tuple[dict[str, object], ...]
    simulated_execution: tuple[TradeRecord, ...]
    portfolio_valuation: tuple[ValuationRecord, ...]
    performance_calculation: tuple[PerformanceRecord, ...]
    survivorship_warning: bool
    affected_quality: tuple[dict[str, object], ...]
    disclaimer: str = "Research estimate, not investment advice."

    def as_dict(self) -> dict[str, object]:
        return {
            "disclosure": self.disclosure.as_dict(),
            "signal_generation": [canonical_value(row) for row in self.signal_generation],
            "simulated_execution": [canonical_value(self._trade_dict(row)) for row in self.simulated_execution],
            "portfolio_valuation": [canonical_value(row.__dict__) for row in self.portfolio_valuation],
            "performance_calculation": [canonical_value(row.__dict__) for row in self.performance_calculation],
            "survivorship_warning": self.survivorship_warning,
            "affected_quality": [canonical_value(row) for row in self.affected_quality],
            "disclaimer": self.disclaimer,
        }

    def _trade_dict(self, row: TradeRecord) -> dict[str, Any]:
        return {
            "trading_date": row.trading_date,
            "instrument": row.instrument,
            "direction": row.direction,
            "requested_quantity": row.requested_quantity,
            "filled_quantity": row.filled_quantity,
            "reason": row.reason,
            "execution_price": row.execution_price,
            "gross_value": row.gross_value,
            "cost_components": dict(row.cost_components),
            "total_cost": row.total_cost,
            "net_cash_change": row.net_cash_change,
        }


_UNSUPPORTED_CAPABILITIES = frozenset(
    {"short_selling", "leverage", "intraday_execution", "derivatives"}
)


def _round(value: Decimal, precision: int, rounding: str) -> Decimal:
    try:
        return value.quantize(Decimal(1).scaleb(-precision), rounding=rounding)
    except (InvalidOperation, ValueError) as error:
        raise ValueError("quantization failed") from error
# ruff: noqa: PLR0912 PLR0913 PLR0915


@dataclass(frozen=True, slots=True)
class BacktestEngine:
    strategy: Strategy
    calendar: TradingCalendarVersion
    bars: Sequence[DailyBar]
    tradability: Sequence[Tradability]
    cost_model: CostModel
    missing_price_policy: MissingPricePolicy
    initial_cash: Decimal
    initial_positions: Mapping[str, Decimal]
    point_in_time_membership: Mapping[date, frozenset[str]] | None = None
    entries: list[TradeRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.initial_cash < Decimal(0):
            raise ValueError("initial cash must not be negative")
        if any(value < Decimal(0) for value in self.initial_positions.values()):
            raise ValueError("initial positions must not be negative")
        if self.missing_price_policy not in ("UNAVAILABLE", "FIVE_SESSION_FALLBACK"):
            raise ValueError("missing-price policy must be a supported option")
        if any(bar.trading_date not in self.calendar.open_dates for bar in self.bars):
            raise ValueError("daily bars must use open trading sessions")


    def run(self) -> Result[BacktestReport, UnsupportedMVP | InvalidRequest]:
        unsupported = self.strategy.required_capabilities & _UNSUPPORTED_CAPABILITIES
        if unsupported:
            return Success(self._zero_trade_report(unsupported))
        if not self.strategy.api_version or not self.calendar.version_id:
            return Failure(InvalidRequest("strategy and calendar versions are required"))

        bars_by_date: dict[date, dict[str, DailyBar]] = {}
        for bar in self.bars:
            bars_by_date.setdefault(bar.trading_date, {})[bar.instrument] = bar
        tradability_by_date: dict[date, dict[str, Tradability]] = {}
        for status in self.tradability:
            tradability_by_date.setdefault(status.trading_date, {})[status.instrument] = status

        cash = self.initial_cash
        positions = dict(self.initial_positions)
        generate_records: list[dict[str, object]] = []
        trades: list[TradeRecord] = []
        valuations: list[ValuationRecord] = []
        performances: list[PerformanceRecord] = []
        previous_value: Decimal | None = None
        running_max: Decimal | None = None
        pending: list[PendingSignal] = []

        for trading_date in self.calendar.dates:
            bars = bars_by_date.get(trading_date, {})
            view = AsOfMarketView(self.bars, trading_date)
            reciprocal_positions = {
                instrument: positions.get(instrument, Decimal(0)) for instrument in self._universe()
            }
            context = DayContext(
                trading_date=trading_date,
                history=view,
                positions=reciprocal_positions,
                cash=cash,
            )
            while pending:
                due = pending.pop(0)
                if due.execution_date != trading_date:
                    continue
                record, _cost, cash_delta, quantity_delta = self._execute_signal(
                    trading_date,
                    due.signal,
                    bars.get(due.signal.instrument),
                    tradability_by_date.get(trading_date, {}).get(due.signal.instrument),
                    positions.get(due.signal.instrument, Decimal(0)),
                    cash,
                )
                trades.append(record)
                cash += cash_delta
                next_quantity = positions.get(due.signal.instrument, Decimal(0)) + quantity_delta
                if next_quantity > 0:
                    positions[due.signal.instrument] = next_quantity
                elif due.signal.instrument in positions:
                    positions.pop(due.signal.instrument)

            current_signals = list(self.strategy.on_day_close(context))
            generate_records.append(
                {"trading_date": trading_date, "signals": list(current_signals)}
            )
            for signal in current_signals:
                next_date = self._next_open_session(trading_date)
                if next_date is not None:
                    pending.append(PendingSignal(trading_date, next_date, signal))

            for instrument in self._universe():
                valuation = self._value_instrument(trading_date, instrument, bars.get(instrument), positions.get(instrument, Decimal(0)))
                valuations.append(valuation)
            universe = self._universe()
            unavailable = any(not row.valuation_available for row in valuations[-len(universe):])
            portfolio_value = None if unavailable else sum(
                (row.value for row in valuations[-len(universe):]), Decimal(0)
            ) + cash
            if portfolio_value is None:
                performance = PerformanceRecord(trading_date, False, None, None, None)
            else:
                simple_return = (
                    None if previous_value is None or previous_value == 0 else portfolio_value / previous_value - 1
                )
                if previous_value is not None and previous_value != 0:
                    if running_max is None or portfolio_value > running_max:
                        running_max = portfolio_value
                    drawdown = portfolio_value / running_max - 1
                else:
                    running_max = Decimal(0) if previous_value == 0 else running_max
                    drawdown = None
                performance = PerformanceRecord(trading_date, True, portfolio_value, simple_return, drawdown)
            if performance.available:
                previous_value = portfolio_value
                running_max = max(running_max or Decimal(0), portfolio_value)
            performances.append(performance)

        survivorship = any(
            self.point_in_time_membership is None
            or instrument not in self.point_in_time_membership.get(trading_date, frozenset())
            for trading_date in self.calendar.dates
            for instrument in self._universe()
        )
        used_quality = [
            {"instrument": instrument, "date": trading_date, "status": bar.quality_status}
            for trading_date in self.calendar.dates
            for instrument, bar in bars_by_date.get(trading_date, {}).items()
            if bar.quality_status in ("WARNING", "REJECTED")
        ]
        dates = self.calendar.dates
        disclosure = BacktestDisclosure(
            data_start=dates[0],
            data_end=dates[-1],
            universe=self._universe(),
            benchmark="NONE",
            calendar_version=self.calendar.version_id,
            adjustment_mode="Es",
            cost_model=self.cost_model,
            missing_price_policy=self.missing_price_policy,
        )
        return Success(
            BacktestReport(
                disclosure=disclosure,
                signal_generation=tuple(generate_records),
                simulated_execution=tuple(trades),
                portfolio_valuation=tuple(valuations),
                performance_calculation=tuple(performances),
                survivorship_warning=survivorship,
                affected_quality=tuple(used_quality),
            )
        )

    def _universe(self) -> frozenset[str]:
        return frozenset(bar.instrument for bar in self.bars)

    def _next_open_session(self, anchor: date) -> date | None:
        dates = self.calendar.dates
        try:
            start = dates.index(anchor) + 1
        except ValueError:
            return None
        return dates[start] if start < len(dates) else None

    def _zero_trade_report(self, unsupported: frozenset[str]) -> BacktestReport:
        dates = self.calendar.dates
        if not dates:
            raise ValueError("trading calendar requires open dates")
        disclosure = BacktestDisclosure(
            data_start=dates[0],
            data_end=dates[-1],
            universe=self._universe(),
            benchmark="NONE",
            calendar_version=self.calendar.version_id,
            adjustment_mode="NONE",
            cost_model=self.cost_model,
            missing_price_policy=self.missing_price_policy,
        )
        valuations: list[ValuationRecord] = []
        performances: list[PerformanceRecord] = []
        for trading_date in dates:
            performances.append(PerformanceRecord(trading_date, False, None, None, None))
        return BacktestReport(
            disclosure=disclosure,
            signal_generation=(),
            simulated_execution=(),
            portfolio_valuation=tuple(valuations),
            performance_calculation=tuple(performances),
            survivorship_warning=False,
            affected_quality=(),
        )

    def _execute_signal(
        self,
        trading_date: date,
        signal: Signal,
        bar: DailyBar | None,
        tradability: Tradability | None,
        held_quantity: Decimal,
        cash: Decimal,
    ) -> tuple[TradeRecord, Decimal, Decimal, Decimal]:
        if bar is None or bar.close <= 0 or signal.requested_quantity <= 0:
            return self._blocked_trade(trading_date, signal, "INVALID_REQUEST")
        blocked = self._blocked_reason(tradability, signal.direction, held_quantity)
        if blocked is not None:
            return self._blocked_trade(trading_date, signal, blocked)

        slip_percentage = self.cost_model.slippage_bps / Decimal(10000)
        slip = bar.close * slip_percentage
        execution_price = (
            _round(bar.close + slip, self.cost_model.price_precision, self.cost_model.price_rounding)
            if signal.direction == "BUY"
            else _round(bar.close - slip, self.cost_model.price_precision, self.cost_model.price_rounding)
        )
        gross = _round(signal.requested_quantity * execution_price, self.cost_model.currency_precision, self.cost_model.currency_rounding)
        commission = max(self.cost_model.minimum_fee, _round(gross * self.cost_model.commission_rate, self.cost_model.currency_precision, self.cost_model.currency_rounding))
        tax = _round(gross * self.cost_model.tax_rate, self.cost_model.currency_precision, self.cost_model.currency_rounding)
        total_cost = _round(commission + tax, self.cost_model.currency_precision, self.cost_model.currency_rounding)
        cash_needed = _round(gross + total_cost, self.cost_model.currency_precision, self.cost_model.currency_rounding)
        if signal.direction == "BUY" and cash < cash_needed:
            return self._blocked_trade(trading_date, signal, "INSUFFICIENT_CASH")

        cash_change = cash_needed if signal.direction == "BUY" else _round(gross - total_cost, self.cost_model.currency_precision, self.cost_model.currency_rounding)
        record = TradeRecord(
            trading_date=trading_date,
            instrument=signal.instrument,
            direction=signal.direction,
            requested_quantity=signal.requested_quantity,
            filled_quantity=signal.requested_quantity,
            reason="FILLED",
            execution_price=execution_price,
            gross_value=gross,
            cost_components={"commission": commission, "tax": tax},
            total_cost=total_cost,
            net_cash_change=cash_change,
            cash_delta=-cash_change if signal.direction == "BUY" else cash_change,
            position_delta=signal.requested_quantity if signal.direction == "BUY" else -signal.requested_quantity,
        )
        self.entries.append(record)
        return (
            record,
            execution_price,
            -cash_change if signal.direction == "BUY" else cash_change,
            signal.requested_quantity if signal.direction == "BUY" else -signal.requested_quantity,
        )

    def _blocked_reason(self, tradability: Tradability | None, direction: SignalDirection, held_quantity: Decimal) -> str | None:
        status = tradability.status if tradability is not None else "UNKNOWN"
        if status != "OPEN":
            return status
        if direction == "SELL" and held_quantity <= 0:
            return "NO_POSITION"
        return None

    def _blocked_trade(self, trading_date: date, signal: Signal, reason: str) -> tuple[TradeRecord, Decimal | None, Decimal, Decimal]:
        record = TradeRecord(
                trading_date=trading_date,
                instrument=signal.instrument,
                direction=signal.direction,
                requested_quantity=signal.requested_quantity,
                filled_quantity=Decimal(0),
                reason=reason,
                execution_price=None,
                gross_value=None,
                cost_components={"commission": Decimal(0), "tax": Decimal(0)},
                total_cost=Decimal(0),
                net_cash_change=Decimal(0),
            cash_delta=Decimal(0),
            position_delta=Decimal(0),
        )
        self.entries.append(record)
        return (
            record,
            None,
            Decimal(0),
            Decimal(0),
        )

    def _value_instrument(
        self,
        trading_date: date,
        instrument: str,
        bar: DailyBar | None,
        quantity: Decimal,
    ) -> ValuationRecord:
        if bar is not None and bar.close > 0:
            source_date = trading_date
            close = bar.close
        elif self.missing_price_policy == "UNAVAILABLE":
            source_date = None
            close = None
        else:
            source_date = self._fallback_date(trading_date, instrument)
            close = self._bar(source_date, instrument).close if source_date is not None else None
        value = None if close is None else quantity * close
        return ValuationRecord(
            trading_date=trading_date,
            instrument=instrument,
            close=close,
            source_date=source_date,
            valuation_available=close is not None,
            value=value,
        )

    def _fallback_date(self, trading_date: date, instrument: str) -> date | None:
        dates = self.calendar.dates
        index = dates.index(trading_date)
        for prior in reversed(dates[max(0, index - 5): index]):
            bar = self._bar(prior, instrument)
            if bar is not None and bar.close > 0:
                return prior
        return None

    def _bar(self, trading_date: date, instrument: str) -> DailyBar | None:
        return next(
            (bar for bar in self.bars if bar.trading_date == trading_date and bar.instrument == instrument),
            None,
        )
