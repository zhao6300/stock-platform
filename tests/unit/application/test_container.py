from __future__ import annotations

from stock_platform.application.container import ApplicationContainer
from stock_platform.application.status import StatusDiagnostics


def test_container_status_reports_composition_fields() -> None:
    container = ApplicationContainer(
        providers=("alpha", "beta"),
        adapter="alpha-v1",
        contract="1.0.0",
        schema="daily_bar.v1",
        compatible_schemas=("daily_bar.v1", "fund_nav.v1"),
        storage="parquet.v1",
        latest_ingestion="COMPLETED",
    )

    status = container.status()

    assert isinstance(status, StatusDiagnostics)
    assert status.installed == ("alpha", "beta")
    assert status.adapter == "alpha-v1"
    assert status.contract == "1.0.0"
    assert status.schema == "daily_bar.v1"
    assert status.compatible_schemas == ("daily_bar.v1", "fund_nav.v1")
    assert status.storage == "parquet.v1"
    assert status.latest_ingestion == "COMPLETED"


def test_container_status_has_explicit_no_successful_ingestion() -> None:
    status = ApplicationContainer(providers=("alpha",)).status()

    assert status.latest_ingestion == "NO_SUCCESSFUL_INGESTION"
