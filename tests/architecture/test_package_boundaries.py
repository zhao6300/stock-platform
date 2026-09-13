from __future__ import annotations

from pathlib import Path


def test_domain_has_no_outer_layer_imports() -> None:
    for path in (Path("src") / "stock_platform" / "domain").glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "stock_platform.application" not in source
        assert "stock_platform.web" not in source
        assert "stock_platform.cli" not in source
        assert "stock_platform.infrastructure" not in source
        assert "stock_platform.providers" not in source


def test_application_has_no_interface_or_infrastructure_imports() -> None:
    for path in (Path("src") / "stock_platform" / "application").glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "stock_platform.web" not in source
        assert "stock_platform.cli" not in source
        assert "stock_platform.infrastructure" not in source
