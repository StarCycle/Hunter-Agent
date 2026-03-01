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

from hunter_agent.arxiv.client import ArxivClient  # noqa: E402
from hunter_agent.arxiv.parser import ArxivHtmlParser  # noqa: E402
from hunter_agent.config import get_settings  # noqa: E402
from hunter_agent.db.repo import TalentRepository  # noqa: E402
from hunter_agent.skills.arxiv_robotics_daily_collector import (  # noqa: E402
    run_arxiv_robotics_daily_collector,
)


def main() -> None:
    raw = sys.stdin.read().strip()
    payload = json.loads(raw) if raw else {}
    settings = get_settings()
    repo = TalentRepository(db_path=settings.db_path)
    repo.init_db()
    result = run_arxiv_robotics_daily_collector(
        payload=payload,
        arxiv_client=ArxivClient(
            timeout_seconds=settings.http_timeout_seconds,
            max_results=settings.arxiv_max_results,
            local_timezone=settings.arxiv_local_timezone,
        ),
        html_parser=ArxivHtmlParser(timeout_seconds=settings.http_timeout_seconds),
        repo=repo,
        persist_mentions=bool(payload.get("persist_mentions", False)),
    )
    sys.stdout.write(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
