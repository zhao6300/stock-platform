from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import typer

from stock_platform.application.ai import AIAnalysisRequest, execute_ai_analysis
from stock_platform.application.container import ApplicationContainer
from stock_platform.application.queries import QueryFilter
from stock_platform.domain.ai import parse_ai_analysis_intent
from stock_platform.domain.common import Failure
from stock_platform.domain.research import DataSnapshotManifest
from stock_platform.infrastructure.ai.reasoner import LocalEvidenceReasoner


@dataclass(frozen=True, slots=True)
class CliContext:
    """A tiny injectable context for local, read-only commands."""

    container: ApplicationContainer


context = CliContext(ApplicationContainer(ai_reasoner=LocalEvidenceReasoner()))


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
    credential_reference: str = typer.Option(
        ..., prompt=False, help="Required Keychain reference."
    ),
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


def _parse_filter(text: str) -> QueryFilter:
    """Parse one exact-match AI query filter."""
    field, separator, value = text.partition("=")
    if not separator or not field:
        raise typer.BadParameter("filter must use field=value")
    return QueryFilter(field, value)


@app.command(name="ai-analyze")
def ai_analyze(
    entity: str,
    snapshot_id: str,
    sort_field: str,
    intent: str = "OVERVIEW",
    filters: list[str] = typer.Option(default_factory=list, metavar="FILTER", help="field=value."),  # noqa: B008
) -> None:
    """Run the deterministic local evidence reasoner against a pinned snapshot."""
    try:
        filter_values = tuple(_parse_filter(text) for text in filters)
        intent_type = parse_ai_analysis_intent(intent)
    except typer.BadParameter as error:
        typer.echo(f"error={error}", err=True)
        raise typer.Exit(code=2) from error
    if intent_type is None:
        typer.echo(f"error=unsupported AI intent: {intent}", err=True)
        raise typer.Exit(code=2) from None
    request = AIAnalysisRequest(
        entity=entity,
        snapshot_id=snapshot_id,
        intent=intent_type,
        sort_field=sort_field,
        filters=filter_values,
    )
    result = execute_ai_analysis(
        request,
        context.container.catalog,
        context.container.snapshots,
        context.container.require_ai_reasoner(),
    )
    if isinstance(result, Failure):
        typer.echo(f"error={result.error.statement}", err=True)
        raise typer.Exit(code=2) from None
    artifact = result.value
    analysis_id = context.container.record_ai_analysis(artifact)
    typer.echo(f"analysis={analysis_id}")
    typer.echo(f"model={artifact.model_id} findings={len(artifact.findings)}")
