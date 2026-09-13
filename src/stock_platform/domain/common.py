from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from json import dumps
from math import isfinite

from stock_platform.domain.fundamentals import SeriesPoint as SeriesPoint

type JsonObject = dict[str, JsonValue]
type JsonValue = None | bool | int | float | str | JsonObject | JsonArray
type JsonArray = list[JsonValue]


@dataclass(frozen=True, slots=True)
class Success[ValueT]:
    """Successful typed result."""

    value: ValueT


@dataclass(frozen=True, slots=True)
class Failure[OutcomeT]:
    """Failed typed result."""

    error: OutcomeT


type Result[ValueT, OutcomeT] = Success[ValueT] | Failure[OutcomeT]


def _mean(values: Sequence[Decimal]) -> Decimal:
    """Calculate the mean of a non-empty Decimal sequence."""
    if not values:
        raise ValueError("values must not be empty")
    return sum(values, Decimal(0)) / len(values)


def _drawdown(values: Sequence[Decimal]) -> Sequence[Decimal]:
    """Return drawdown series."""
    maximum: Decimal = Decimal(0)
    running = Decimal(0)
    result: list[Decimal] = []
    for value in values:
        running = max(running, value)
        maximum = max(maximum, value)
        result.append(value / maximum - 1)
    return result


def canonical_value(value: object) -> JsonValue:
    """Convert a platform-owned value to a deterministic JSON-compatible value."""
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("finite numbers only")
        return float(value)
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("finite numbers only")
        return format(value.normalize(), "f")
    if isinstance(value, datetime):
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("datetime values must be timezone-aware")
        if value.tzinfo is not UTC:
            value = value.astimezone(UTC)
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        encoded = {str(key): canonical_value(inner) for key, inner in value.items()}
        return {key: encoded[key] for key in sorted(encoded)}
    if isinstance(value, (tuple, list, set, frozenset)):
        values = [canonical_value(inner) for inner in value]
        if isinstance(value, (set, frozenset)):
            values.sort(key=lambda item: dumps(item, sort_keys=True, allow_nan=False))
        return values
    raise ValueError(f"unsupported canonical JSON type: {type(value).__name__}")


def canonical_json(value: object) -> str:
    """Return UTF-8 canonical JSON with sorted keys and schema-safe scalars."""
    return dumps(
        canonical_value(value),
        ensure_ascii=False,
        indent=None,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def unpack[ValueT, ErrorT: BaseException](result: Result[ValueT, ErrorT]) -> ValueT:
    """Discriminate a success result or raise the failure error."""
    if isinstance(result, Success):
        return result.value
    raise result.error


def ensure_timezone_aware(value: datetime) -> datetime:
    """Reject naive datetimes and preserve their timezone-aware value."""
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError("datetime values must be timezone-aware")
    return value
