from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.infrastructure.backup.manifest import (
    BackupManifest,
    DatasetManifest,
    restore_eligible,
)


@given(
    compatible=st.booleans(),
    matching_checksum=st.booleans(),
    matching_bytes=st.booleans(),
    schema=st.sampled_from(("schema-v1", "schema-v2")),
)
def test_restore_eligibility_requires_compatibility_and_verification(
    compatible: bool,
    matching_checksum: bool,
    matching_bytes: bool,
    schema: str,
) -> None:
    content = b"row"
    checksum = sha256(content).hexdigest() if matching_checksum else "0" * 64
    target_schema = "schema-v1" if compatible else "schema-v2"
    dataset = DatasetManifest(
        name=schema,
        schema_id=target_schema,
        rows=1,
        sha256=checksum,
        bytes=len(content) if matching_bytes else len(content) + 1,
    )
    manifest = BackupManifest(schema_id=target_schema, datasets=(dataset,))
    directory = Path("/tmp")
    directory.joinpath(dataset.name).write_bytes(content)

    result = restore_eligible(manifest, ("schema-v1",), directory)

    if compatible and matching_checksum and matching_bytes:
        assert result.value == target_schema
    else:
        assert result.error is not None
