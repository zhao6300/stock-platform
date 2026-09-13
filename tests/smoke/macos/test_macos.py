from pathlib import Path

import pytest


@pytest.mark.macos


def test_macos_smoke_requirements_are_recorded() -> None:
    docs = (Path(__file__).parents[3] / "docs" / "tasks.md").read_text()

    for task in (
        "6.11 Implement Keychain credential references, selective deletion, and recursive Secret Redactor",
        "12.4 Validate Web/OpenAPI/CLI local-only and no-trading surfaces",
        "13.3 Implement optional encrypted credential capsule failure semantics",
        "13.8 Add macOS owner-permission and Keychain smoke tests",
    ):
        assert docs.count(f"- [x] {task}") >= 1
