from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from stock_platform.application.container import ApplicationContainer
from stock_platform.application.queries import QueryFilter, ResearchQuery, execute_research_query
from stock_platform.application.status import StatusDiagnostics
from stock_platform.domain.common import Success

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


@app.get("/", response_class=HTMLResponse)
async def research_page() -> str:
    """Return the local-only research shell with required labels."""
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Personal Stock & Fund Research Platform</title>
  </head>
  <body>
    <main>
      <h1>Local Research Platform</h1>
      <p><strong>Adjustment mode:</strong> UNADJUSTED</p>
      <p><strong>Data quality:</strong> DATA_QUALITY_NOT_ASSESSED</p>
      <p><strong>Provider:</strong> UNCONFIGURED</p>
      <p><strong>Status:</strong> {container.status().latest_ingestion}</p>
      <p><strong>Research estimate disclaimer:</strong> Research estimate, not investment advice.</p>
    </main>
  </body>
</html>"""


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
