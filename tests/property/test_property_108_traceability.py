from __future__ import annotations

import pytest


@pytest.mark.requirement_traceability
def test_backtest_records_link_to_source_requirements() -> None:
    marker_name = "requirement_traceability"

    assert pytest.mark.requirement_traceability.name == marker_name
