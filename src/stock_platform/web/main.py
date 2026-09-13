from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from stock_platform.application.container import ApplicationContainer
from stock_platform.application.status import StatusDiagnostics

container = ApplicationContainer()
app = FastAPI(title="Personal Stock & Fund Research Platform")


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
async def status() -> StatusDiagnostics:
    return container.status()
