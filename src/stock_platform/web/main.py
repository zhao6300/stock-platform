from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from jinja2 import BaseLoader, Environment
from pydantic import BaseModel, Field

from stock_platform.application.container import ApplicationContainer
from stock_platform.application.queries import QueryFilter, ResearchQuery, execute_research_query
from stock_platform.application.status import StatusDiagnostics
from stock_platform.domain.common import Success
from stock_platform.domain.research import (
    DataObjectReference,
    DataSnapshotManifest,
)
from stock_platform.web.access import enforce_loopback

jinja2_environment = Environment(loader=BaseLoader())

container = ApplicationContainer()
app = FastAPI(title="Personal Stock & Fund Research Platform")


class QueryFilterRequest(BaseModel):
    """One typed exact-match query parameter."""

    field: str
    value: str
    model_config = {"extra": "forbid"}


class ResearchQueryRequest(BaseModel):
    """The local API query boundary."""

    entity: str
    snapshot_id: str
    sort_field: str
    filters: tuple[QueryFilterRequest, ...] = Field(default=(), max_length=20)
    model_config = {"extra": "forbid"}

    def to_domain(self) -> ResearchQuery:
        return ResearchQuery(
            entity=self.entity,
            snapshot_id=self.snapshot_id,
            sort_field=self.sort_field,
            filters=tuple(QueryFilter(item.field, item.value) for item in self.filters),
        )


class ResearchQueryResponse(BaseModel):
    """A stable bounded read-only query result."""

    snapshot_id: str
    entity: str
    query_parameters: str
    applied_filter_count: int
    returned_count: int
    rows: tuple[tuple[tuple[str, object], ...], ...]
    has_more: bool


class DataObjectReferenceRequest(BaseModel):
    """One immutable content-addressed artifact."""

    sha256: str
    schema_id: str
    rows: int


class CredentialSetRequest(BaseModel):
    """Store one secret-backed credential reference."""

    reference: str
    model_config = {"extra": "forbid"}


class SnapshotCreateRequest(BaseModel):
    """Freeze one immutable snapshot manifest."""

    dataset_version_id: str
    objects: tuple[DataObjectReferenceRequest, ...] = ()
    security_master_versions: tuple[str, ...] = ()
    mapping_versions: tuple[str, ...] = ()
    calendar_versions: tuple[str, ...] = ()
    factor_series_versions: tuple[str, ...] = ()
    quality_rule_set_version: str
    quality_assessment_cutoff: datetime
    model_config = {"extra": "forbid"}

    def to_domain(self) -> DataSnapshotManifest:
        return DataSnapshotManifest(
            dataset_version_id=self.dataset_version_id,
            objects=tuple(
                DataObjectReference(
                    sha256=item.sha256,
                    schema_id=item.schema_id,
                    rows=item.rows,
                )
                for item in self.objects
            ),
            security_master_versions=self.security_master_versions,
            mapping_versions=self.mapping_versions,
            calendar_versions=self.calendar_versions,
            factor_series_versions=self.factor_series_versions,
            quality_rule_set_version=self.quality_rule_set_version,
            quality_assessment_cutoff=self.quality_assessment_cutoff,
        )


class ProviderConfigureRequest(BaseModel):
    """Install a provider configuration."""

    endpoint: str
    credential_reference: str | None = None
    enabled: bool = False
    model_config = {"extra": "forbid"}


class ProviderEnableRequest(BaseModel):
    """Atomically switch to one configured candidate provider."""

    contract_version: str
    model_config = {"extra": "forbid"}


@app.get("/api/v1/providers")
async def list_providers(request: Request) -> dict[str, tuple[str, ...]]:
    """Return every configured provider without secret material."""
    enforce_loopback(request)
    return {"providers": container.providers}


@app.post("/api/v1/providers/{provider_id}/configure")
async def configure_provider(
    provider_id: str, body: ProviderConfigureRequest, request: Request
) -> dict[str, object]:
    """Install or refresh one provider configuration locally."""
    enforce_loopback(request, write=True)
    configuration: Mapping[str, Any] = container.configure_provider(
        provider_id,
        {
            "endpoint": body.endpoint,
            "credential_reference": body.credential_reference,
        },
    )
    return {
        "provider": provider_id,
        "configuration": dict(configuration),
    }


@app.post("/api/v1/providers/{provider_id}/enable")
async def enable_provider(
    provider_id: str, body: ProviderEnableRequest, request: Request
) -> dict[str, object]:
    """Atomically activate one configured provider and pin its contract."""
    enforce_loopback(request, write=True)
    try:
        return dict(container.enable_provider(provider_id, body.contract_version))
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@app.post("/api/v1/credentials", status_code=status.HTTP_201_CREATED)
async def set_credential(body: CredentialSetRequest, request: Request) -> dict[str, str]:
    """Store a Keychain reference; never echo or expose secret bytes."""
    enforce_loopback(request, write=True)
    container.credential_references = frozenset((*container.credential_references, body.reference))
    return {"reference": body.reference}


@app.delete("/api/v1/credentials/{reference}")
async def delete_credential(reference: str, request: Request) -> dict[str, str]:
    """Remove exactly the selected credential reference."""
    enforce_loopback(request, write=True)
    container.credential_references = frozenset(
        item for item in container.credential_references if item != reference
    )
    return {"deleted": reference}


@app.post("/api/v1/snapshots", status_code=status.HTTP_201_CREATED)
async def create_snapshot(body: SnapshotCreateRequest, request: Request) -> dict[str, str]:
    """Freeze one snapshot and return only its canonical ID."""
    enforce_loopback(request, write=True)
    snapshot_id = container.create_snapshot(body.to_domain())
    return {"snapshot_id": snapshot_id}


@app.post("/api/v1/snapshots/{snapshot_id}/confirm-rejected")
async def confirm_rejected_snapshot(snapshot_id: str, request: Request) -> dict[str, str]:
    """Record explicit confirmation for one pinned rejected snapshot."""
    enforce_loopback(request, write=True)
    try:
        container.confirm_rejected_snapshot(snapshot_id)
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    return {"snapshot_id": snapshot_id}


@app.get("/", response_class=HTMLResponse)
async def research_page() -> str:
    """Return the local-only research shell with required labels."""
    template = jinja2_environment.from_string(
        """<!doctype html>
<html lang="en">
  <body>
    <h1>Local Research Platform</h1>
    <p>Adjustment mode: {{ adjustment_mode }}</p>
    <p>Data quality: {{ quality }}</p>
    <p>Research estimate, not investment advice.</p>
  </body>
</html>"""
    )
    return template.render(
        adjustment_mode="UNADJUSTED",
        quality="DATA_QUALITY_NOT_ASSESSED",
    )


@app.get("/api/v1/status")
async def get_status() -> StatusDiagnostics:
    return container.status()


@app.post("/api/v1/research/query")
async def research_query(body: ResearchQueryRequest) -> ResearchQueryResponse:
    result = execute_research_query(body.to_domain(), container.catalog)
    if isinstance(result, Success):
        value = result.value
        return ResearchQueryResponse(
            snapshot_id=value.snapshot_id,
            entity=value.entity,
            query_parameters=value.query_parameters,
            applied_filter_count=value.applied_filter_count,
            returned_count=value.returned_count,
            rows=value.rows,
            has_more=value.has_more,
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="query limits exceeded",
    )
