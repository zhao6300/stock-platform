from __future__ import annotations

from typing import TypedDict


class BackupPlatformState(TypedDict):
    schema_id: str
    configuration: tuple[str, ...]
    security_master_versions: tuple[str, ...]
    security_mappings: tuple[str, ...]
    calendars: tuple[str, ...]
    retained_data: tuple[str, ...]
    quality_reports: tuple[str, ...]
    snapshot_ids: tuple[str, ...]
    manifests: tuple[str, ...]
    research_results: tuple[str, ...]
    credentials: tuple[str, ...]
