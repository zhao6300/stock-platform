from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.infrastructure.backup.backup import (
    BackupPlatformState,
    default_backup_manifest,
)


@given(
    state_values=st.tuples(
        st.lists(st.text(min_size=1), max_size=10),
        st.lists(st.text(min_size=1), max_size=10),
        st.lists(st.text(min_size=1), max_size=10),
        st.lists(st.text(min_size=1), max_size=10),
        st.lists(st.text(min_size=1), max_size=10),
        st.lists(st.text(min_size=1), max_size=10),
        st.lists(st.text(min_size=1), max_size=10),
        st.lists(st.text(min_size=1), max_size=10),
        st.lists(st.text(min_size=1), max_size=10),
        st.lists(st.text(min_size=1), max_size=10),
    ),
)
def test_default_backup_inventory_is_complete_and_secret_free(
    state_values: tuple[
        list[str],
        list[str],
        list[str],
        list[str],
        list[str],
        list[str],
        list[str],
        list[str],
        list[str],
        list[str],
    ],
) -> None:
    (
        configuration,
        security_master_versions,
        security_mappings,
        calendars,
        retained_data,
        quality_reports,
        snapshot_ids,
        manifests,
        research_results,
        credentials,
    ) = state_values
    state = BackupPlatformState(
        schema_id="schema-v1",
        configuration=tuple(configuration),
        security_master_versions=tuple(security_master_versions),
        security_mappings=tuple(security_mappings),
        calendars=tuple(calendars),
        retained_data=tuple(retained_data),
        quality_reports=tuple(quality_reports),
        snapshot_ids=tuple(snapshot_ids),
        manifests=tuple(manifests),
        research_results=tuple(research_results),
        credentials=tuple(credentials),
    )

    manifest = default_backup_manifest(state)

    dataset_names = {dataset.name for dataset in manifest.datasets}
    assert dataset_names == {
        "configuration",
        "security_master_versions",
        "security_mappings",
        "calendars",
        "retained_data",
        "quality_reports",
        "snapshot_ids",
        "manifests",
        "research_results",
    }
    assert "credentials" not in dataset_names
    assert all(
        "credentials" not in dataset.name and "credential" not in dataset.name
        for dataset in manifest.datasets
    )
