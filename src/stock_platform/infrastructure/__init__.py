"""Technology-specific implementations behind application ports."""

for _subpackage in ("sqlite", "parquet", "query", "network", "secrets", "backup", "observability"):
    # These boundaries are intentionally empty until their owning task adds them.
    __import__("os").makedirs(_subpackage, exist_ok=True)
