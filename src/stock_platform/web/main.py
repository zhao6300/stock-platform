from __future__ import annotations

from fastapi import FastAPI

from stock_platform.application.container import ApplicationContainer
from stock_platform.application.status import StatusDiagnostics

container = ApplicationContainer()
app = FastAPI(title="Personal Stock & Fund Research Platform")


@app.get("/api/v1/status")
async def status() -> StatusDiagnostics:
    return container.status()
