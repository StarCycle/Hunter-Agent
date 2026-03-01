from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path
    export_dir: Path
    arxiv_max_results: int
    http_timeout_seconds: int


def get_settings() -> Settings:
    db_path = Path(os.getenv("HUNTER_DB_PATH", "data/hunter.db"))
    export_dir = Path(os.getenv("HUNTER_EXPORT_DIR", "exports"))
    arxiv_max_results = int(os.getenv("HUNTER_ARXIV_MAX_RESULTS", "2000"))
    http_timeout_seconds = int(os.getenv("HUNTER_HTTP_TIMEOUT_SECONDS", "20"))
    return Settings(
        db_path=db_path,
        export_dir=export_dir,
        arxiv_max_results=arxiv_max_results,
        http_timeout_seconds=http_timeout_seconds,
    )
