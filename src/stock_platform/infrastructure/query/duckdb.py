from __future__ import annotations

from typing import Any


class DuckDBQueryService:
    """Read-forward gateway for the pure Arrow query service."""

    def __init__(self, arrow: Any, rows: Any = None, snapshot_id: str = "default") -> None:
        self._arrow = arrow
        self._and = (rows, snapshot_id)
