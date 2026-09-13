from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import typer

from stock_platform.application.container import ApplicationContainer
from stock_platform.domain.research import DataSnapshotManifest


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


@app.command(name="provider-list")
def provider_list() -> None:
    """Print installed provider identifiers without reading secrets."""
    for provider in context.container.providers:
        typer.echo(provider)


@app.command(name="provider-configure")
def provider_configure(
    provider: str,
    endpoint: str,
    credential_reference: str = typer.Option(..., prompt=False, help="Required Keychain reference."),
) -> None:
    """Record one local provider configuration and credential reference."""
    configuration = context.container.configure_provider(
        provider,
        {
            "endpoint": endpoint,
            "credential_reference": credential_reference,
        },
    )
    typer.echo(f"configured provider={provider} configuration={configuration}")


@app.command(name="provider-enable")
def provider_enable(
    provider: str,
    contract_version: str,
) -> None:
    """Atomically activate one configured provider."""
    try:
        result = context.container.enable_provider(provider, contract_version)
    except LookupError as error:
        typer.echo(f"error={error}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(f"enabled provider={result['provider']} contract={result['contract']}")


@app.command(name="snapshot-create")
def snapshot_create(
    dataset_version_id: str,
    quality_rule_set_version: str,
    quality_assessment_cutoff: str,
) -> None:
    """Create one local empty-manifest snapshot and print its ID."""
    try:
        cutoff = datetime.fromisoformat(quality_assessment_cutoff)
    except ValueError as error:
        typer.echo("error=quality_assessment_cutoff must be ISO 8601")
        raise typer.Exit(code=2) from error
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=UTC)
    snapshot = DataSnapshotManifest(
        dataset_version_id=dataset_version_id,
        objects=(),
        security_master_versions=(),
        mapping_versions=(),
        calendar_versions=(),
        factor_series_versions=(),
        quality_rule_set_version=quality_rule_set_version,
        quality_assessment_cutoff=cutoff,
    )
    typer.echo(context.container.create_snapshot(snapshot))


@app.command(name="snapshot-confirm")
def snapshot_confirm(snapshot_id: str) -> None:
    """Confirm one pinned snapshot explicitly."""
    try:
        confirmed = context.container.confirm_rejected_snapshot(snapshot_id)
    except LookupError as error:
        typer.echo(f"error={error}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(f"confirmed snapshot_id={snapshot_id} confirmed={confirmed}")
