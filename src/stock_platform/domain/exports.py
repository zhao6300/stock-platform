from __future__ import annotations

from enum import StrEnum


class RetentionPermission(StrEnum):
    """What kind of provider data the legal profile allows to persist."""

    PROHIBITED = "PROHIBITED"
    NORMALIZED_PROVIDER_DATA = "NORMALIZED_PROVIDER_DATA"
    RAW_AND_NORMALIZED_PROVIDER_DATA = "RAW_AND_NORMALIZED_PROVIDER_DATA"
    RAW_PROVIDER_DATA = "RAW_PROVIDER_DATA"


class ExportPermission(StrEnum):
    """What kind of provider data the legal profile allows to export."""

    PROHIBITED = "PROHIBITED"
    DERIVED_RESULTS_ONLY = "DERIVED_RESULTS_ONLY"
    NORMALIZED_PROVIDER_DATA = "NORMALIZED_PROVIDER_DATA"
    RAW_PROVIDER_DATA = "RAW_PROVIDER_DATA"
