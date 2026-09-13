from __future__ import annotations

from datetime import UTC, datetime

from fastapi import status
from fastapi.testclient import TestClient

from stock_platform.domain.research import DataObjectReference, DataSnapshotManifest
from stock_platform.web.main import app, container

loopback_client = TestClient(app, client=("127.0.0.1", 51769))


def test_web_research_query_posts_to_application_use_case() -> None:
    client = loopback_client

    response = client.post(
        "/api/v1/research/query",
        json={
            "entity": "daily_bar",
            "snapshot_id": "snapshot-1",
            "sort_field": "close",
            "filters": [{"field": "close", "value": "10"}],
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["applied_filter_count"] == 1


def test_web_status_is_enabled_and_no_trading_surfaces_absent() -> None:
    client = loopback_client
    response = client.get("/api/v1/status")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["latest_ingestion"] == "NO_SUCCESSFUL_INGESTION"
    names = {route.path for route in app.routes}
    assert "/api/v1/status" in names
    assert not {"orders", "brokers", "trades/live"} & names


def test_research_page_discloses_required_labels_and_disclaimer() -> None:
    client = loopback_client

    result = client.get("/")

    assert result.status_code == status.HTTP_200_OK
    assert "Adjustment mode" in result.text
    assert "Data quality" in result.text
    assert "Research estimate, not investment advice." in result.text


def test_write_requests_reject_second_user_and_non_loopback_source() -> None:
    second_user_client = TestClient(
        app,
        headers={
            "x-platform-effective-uid": "1001",
            "x-csrf-token": "csrf",
            "idempotency-key": "key",
        },
        client=("127.0.0.1", 51769),
    )
    non_loopback_client = TestClient(app, client=("example.com", 443))

    denied_second_user = second_user_client.post(
        "/api/v1/providers/provider-a/configure", json={"endpoint": "https://a.local"}
    )
    denied_non_loopback = non_loopback_client.post(
        "/api/v1/providers/provider-a/configure",
        json={
            "endpoint": "https://a.local",
        },
        headers={"x-csrf-token": "csrf", "idempotency-key": "key"},
    )

    assert denied_second_user.status_code == status.HTTP_403_FORBIDDEN
    assert denied_second_user.json()["detail"] == "SECOND_USER_DENIED"
    assert denied_non_loopback.status_code == status.HTTP_403_FORBIDDEN
    assert denied_non_loopback.json()["detail"] == "CONFIGURED_ENDPOINT_REQUIRED"


def test_write_requests_require_csrf_and_idempotency_before_business_work() -> None:
    local_client = TestClient(app, client=("127.0.0.1", 51769))

    project_id = container.create_snapshot(
        DataSnapshotManifest(
            dataset_version_id="dataset-1",
            objects=(),
            security_master_versions=(),
            mapping_versions=(),
            calendar_versions=(),
            factor_series_versions=(),
            quality_rule_set_version="rules-v1",
            quality_assessment_cutoff=datetime(2026, 1, 31, tzinfo=UTC),
        )
    )
    response = local_client.post(
        "/api/v1/snapshots",
        json={
            "dataset_version_id": "dataset-1",
            "quality_rule_set_version": "rules-v1",
            "quality_assessment_cutoff": "2026-01-31T00:00:00Z",
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "VALIDATION_FAILED"
    assert project_id.startswith("sha256:")


def test_provider_config_then_enable_is_exposed_through_application_state() -> None:
    configured = container.configure_provider("alpha", {"endpoint": "https://alpha.local"})
    enabled = container.enable_provider("alpha", "adapter-v1")

    assert configured["endpoint"] == "https://alpha.local"
    assert enabled["enabled"] is True
    assert container.contract == "adapter-v1"
    assert "alpha" in container.providers


def test_snapshot_create_and_confirm_use_application_service_state() -> None:
    manifest = DataSnapshotManifest(
        dataset_version_id="dataset-1",
        objects=(DataObjectReference(sha256="0" * 64, schema_id="bars-v1", rows=1),),
        security_master_versions=(),
        mapping_versions=(),
        calendar_versions=(),
        factor_series_versions=(),
        quality_rule_set_version="rules-v1",
        quality_assessment_cutoff=datetime(2026, 1, 31, tzinfo=UTC),
    )
    snapshot_id = container.create_snapshot(manifest)
    confirmed = container.confirm_rejected_snapshot(snapshot_id)

    assert snapshot_id.startswith("sha256:")
    assert confirmed is True
    assert snapshot_id in container.snapshots
    assert snapshot_id in container.reject_confirmations


def test_http_provider_configure_and_enable_routes_use_application_services() -> None:
    client = TestClient(app, client=("127.0.0.1", 51769))
    headers = {"x-csrf-token": "csrf", "idempotency-key": "key"}

    configured = client.post(
        "/api/v1/providers/provider-b/configure",
        json={"endpoint": "https://b.local", "credential_reference": "b-key"},
        headers=headers,
    )
    enabled = client.post(
        "/api/v1/providers/provider-b/enable",
        json={"contract_version": "adapter-v1"},
        headers=headers,
    )

    assert configured.status_code == status.HTTP_200_OK
    assert enabled.status_code == status.HTTP_200_OK
    assert enabled.json() == {
        "provider": "provider-b",
        "enabled": True,
        "contract": "adapter-v1",
    }
    assert enabled.json()["contract"] == "adapter-v1"


def test_http_credential_set_and_delete_routes_use_application_services() -> None:
    client = TestClient(app, client=("127.0.0.1", 51769))
    headers = {"x-csrf-token": "csrf", "idempotency-key": "key"}

    created = client.post(
        "/api/v1/credentials",
        json={"reference": "credential-b"},
        headers=headers,
    )
    deleted = client.delete("/api/v1/credentials/credential-b", headers=headers)

    assert created.status_code == status.HTTP_201_CREATED
    assert created.json() == {"reference": "credential-b"}
    assert deleted.status_code == status.HTTP_200_OK
    assert deleted.json() == {"deleted": "credential-b"}
