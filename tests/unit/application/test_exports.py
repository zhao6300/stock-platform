from __future__ import annotations

from stock_platform.domain.exports import ExportPermission, RetentionPermission


def test_export_permission_enum_values_are_stable() -> None:
    assert ExportPermission.PROHIBITED.value == "PROHIBITED"


def test_retention_permission_enum_values_are_stable() -> None:
    assert RetentionPermission.PROHIBITED.value == "PROHIBITED"
