from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import shutil
import uuid


@contextmanager
def workspace_temp_dir():
    base_dir = Path(__file__).resolve().parent / ".tmp"
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
