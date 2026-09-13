from __future__ import annotations

from dataclasses import dataclass

import typer

from stock_platform.application.container import ApplicationContainer


@dataclass(frozen=True, slots=True)
class CliContext:
    """A tiny injectable context for local, read-only commands."""

    container: ApplicationContainer


context = CliContext(ApplicationContainer())


app = typer.Typer(no_args_is_help=True)


@app.command(name="status")
def status() -> None:
    """Print one local diagnostics line without touching state."""
    diagnostics = context.container.status()
    typer.echo(f"adapter={diagnostics.adapter} latest_ingestion={diagnostics.latest_ingestion}")
