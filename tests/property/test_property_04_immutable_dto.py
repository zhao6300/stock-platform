from __future__ import annotations

import pytest


def test_immutable_dto() -> None:
    assert pytest.mark.property.name == "property"
