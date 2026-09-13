from __future__ import annotations

from fastapi import status
from fastapi.testclient import TestClient

from stock_platform.web.main import app


def test_web_status_is_enabled_and_no_trading_surfaces_absent() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/status")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["latest_ingestion"] == "NO_SUCCESSFUL_INGESTION"
    names = {route.path for route in app.routes}
    assert "/api/v1/status" in names
    assert not {"orders", "brokers", "trades/live"} & names


def test_research_page_discloses_required_labels_and_disclaimer() -> None:
    client = TestClient(app)

    result = client.get("/")

    assert result.status_code == status.HTTP_200_OK
    assert "Adjustment mode" in result.text
    assert "Data quality" in result.text
    assert "Research estimate, not investment advice." in result.text
