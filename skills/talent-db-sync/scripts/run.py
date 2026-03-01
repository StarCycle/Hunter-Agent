from __future__ import annotations

import json
from pathlib import Path
import sys


def _bootstrap_pythonpath() -> None:
    root = Path(__file__).resolve().parents[3]
    src_path = root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


_bootstrap_pythonpath()

from hunter_agent.config import get_settings  # noqa: E402
from hunter_agent.db.repo import TalentRepository  # noqa: E402
from hunter_agent.skills.talent_database_sync import run_talent_database_sync  # noqa: E402


def main() -> None:
    raw = sys.stdin.read().strip()
    payload = json.loads(raw) if raw else {}
    settings = get_settings()
    repo = TalentRepository(db_path=settings.db_path)
    repo.init_db()
    result = run_talent_database_sync(payload=payload, repo=repo)
    sys.stdout.write(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
