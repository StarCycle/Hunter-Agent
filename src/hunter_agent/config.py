from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path
    export_dir: Path
    http_timeout_seconds: int
    arxiv_local_timezone: str


def get_settings() -> Settings:
    db_path = Path(os.getenv("HUNTER_DB_PATH", "data/hunter.db"))
    export_dir = Path(os.getenv("HUNTER_EXPORT_DIR", "exports"))
    http_timeout_seconds = int(os.getenv("HUNTER_HTTP_TIMEOUT_SECONDS", "20"))
    arxiv_local_timezone = os.getenv("HUNTER_ARXIV_LOCAL_TIMEZONE", "Asia/Shanghai")
    return Settings(
        db_path=db_path,
        export_dir=export_dir,
        http_timeout_seconds=http_timeout_seconds,
        arxiv_local_timezone=arxiv_local_timezone,
    )
