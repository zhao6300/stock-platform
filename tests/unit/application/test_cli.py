from __future__ import annotations

from typer.testing import CliRunner

from stock_platform.cli.main import app as application
from stock_platform.cli.main import context


def test_cli_has_no_trading_surfaces_and_read_only_status_commands() -> None:
    commands = {item.name for item in application.registered_commands}
    assert "status" in commands
    assert not {"order", "orders", "broker", "brokers", "trade", "trade-live"} & commands
    result = CliRunner().invoke(application, ["--help"])
    assert result.exit_code == 0
    assert "status" in result.output
    status_result = CliRunner().invoke(application, ["status"])
    assert status_result.exit_code == 0
    assert "latest_ingestion=NO_SUCCESSFUL_INGESTION" in status_result.output


def test_cli_provider_config_and_enable_call_application_services() -> None:
    runner = CliRunner()

    configured = runner.invoke(
        application,
        [
            "provider-configure",
            "alpha",
            "https://alpha.local",
            "--credential-reference",
            "alpha-key",
        ],
    )
    enabled = runner.invoke(
        application,
        ["provider-enable", "alpha", "adapter-v1"],
    )

    assert configured.exit_code == 0
    assert "configured provider=alpha" in configured.output
    assert "alpha-key" in configured.output
    assert enabled.exit_code == 0
    assert "contract=adapter-v1" in enabled.output
    assert "alpha" in context.container.providers
    assert context.container.contract == "adapter-v1"


def test_cli_snapshot_create_and_confirm_call_application_services() -> None:
    runner = CliRunner()

    created = runner.invoke(
        application,
        [
            "snapshot-create",
            "dataset-1",
            "rules-v1",
            "2026-01-31T00:00:00Z",
        ],
    )
    snapshot_id = created.output.strip()
    confirmed = runner.invoke(application, ["snapshot-confirm", snapshot_id])

    assert created.exit_code == 0
    assert snapshot_id.startswith("sha256:")
    assert confirmed.exit_code == 0
    assert "confirmed=True" in confirmed.output
    assert snapshot_id in context.container.snapshots
    assert snapshot_id in context.container.reject_confirmations
