from __future__ import annotations

from typer.testing import CliRunner

from stock_platform.cli.main import app as application


def test_cli_has_only_read_only_status_commands() -> None:
    commands = {item.name for item in application.registered_commands}
    assert commands == {"status"}
    result = CliRunner().invoke(application, [])
    assert result.exit_code == 0
    assert "latest_ingestion=NO_SUCCESSFUL_INGESTION" in result.output
