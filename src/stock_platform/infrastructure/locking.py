"""Local writer locks and related infrastructure primitives."""

from __future__ import annotations

import fcntl
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class WriterLock:
    """Serialize writers on a single lock file without blocking same-user reads."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def acquire(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a+") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                current_uid = os.getuid()
                lock_file.seek(0)
                serialized_uid = lock_file.read().strip()
                if serialized_uid and int(serialized_uid) != current_uid:
                    raise PermissionError("another local user holds the writer lock")
                lock_file.seek(0)
                lock_file.truncate()
                lock_file.write(str(current_uid))
                lock_file.flush()
                yield
            finally:
                lock_file.seek(0)
                lock_file.truncate()
                lock_file.flush()
                fcntl.flock(lock_file, fcntl.LOCK_UN)
