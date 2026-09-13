from __future__ import annotations

import pyarrow as pa  # type: ignore[import-untyped]

_DECIMAL_PRECISION = 38
_DECIMAL_SCALE = 10
_VOLUME_DECIMAL_PRECISION = 38
_VOLUME_DECIMAL_SCALE = 10


def decimal_type() -> pa.DataType:
    return pa.decimal128(_DECIMAL_PRECISION, _DECIMAL_SCALE)


def volume_decimal_type() -> pa.DataType:
    return pa.decimal128(_VOLUME_DECIMAL_PRECISION, _VOLUME_DECIMAL_SCALE)


DAILY_BAR_SCHEMA = pa.schema(
    [
        pa.field("canonical_security_id", pa.string(), nullable=False),
        pa.field("observation_date", pa.date32(), nullable=False),
        pa.field("open", decimal_type(), nullable=False),
        pa.field("high", decimal_type(), nullable=False),
        pa.field("low", decimal_type(), nullable=False),
        pa.field("close", decimal_type(), nullable=False),
        pa.field("volume", volume_decimal_type(), nullable=False),
        pa.field("turnover", volume_decimal_type(), nullable=False),
        pa.field("currency", pa.string(), nullable=False),
        pa.field("provider", pa.string(), nullable=False),
        pa.field("provider_identifier", pa.string(), nullable=False),
        pa.field("source_version", pa.string(), nullable=True),
        pa.field("retrieved_at", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("observation_version_id", pa.string(), nullable=False),
    ]
)

PROVENANCE_FIELDS = (
    "provider",
    "provider_identifier",
    "source_version",
    "retrieved_at",
    "observation_version_id",
)


FUND_NAV_SCHEMA = pa.schema(
    [
        pa.field("canonical_security_id", pa.string(), nullable=False),
        pa.field("observation_date", pa.date32(), nullable=False),
        pa.field("unit_nav", decimal_type(), nullable=False),
        pa.field("cumulative_nav", decimal_type(), nullable=True),
        pa.field("currency", pa.string(), nullable=False),
        pa.field("provider", pa.string(), nullable=False),
        pa.field("provider_identifier", pa.string(), nullable=False),
        pa.field("source_version", pa.string(), nullable=True),
        pa.field("retrieved_at", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("observation_version_id", pa.string(), nullable=False),
    ]
)
