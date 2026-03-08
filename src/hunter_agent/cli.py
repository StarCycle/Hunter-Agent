from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from hunter_agent.arxiv.client import ArxivClient
from hunter_agent.arxiv.parser import ArxivHtmlParser
from hunter_agent.config import get_settings
from hunter_agent.db.repo import TalentRepository
from hunter_agent.services.export_service import ExportService
from hunter_agent.skills.arxiv_robotics_daily_collector import (
    run_arxiv_robotics_daily_collector,
)
from hunter_agent.skills.talent_database_sync import (
    run_talent_database_bulk_upsert,
    run_talent_database_sync,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hunter-agent")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db")

    parser_a = sub.add_parser("arxiv-daily-authors")
    parser_a.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser_a.add_argument(
        "--categories",
        default="cs.RO",
        help="Comma-separated arXiv categories, e.g. cs.RO,cs.AI",
    )
    parser_a.add_argument(
        "--persist-mentions",
        action="store_true",
        help="Persist paper/author mentions to SQLite.",
    )
    parser_a.add_argument("--out-json", default="", help="Optional output JSON path.")

    parser_b_find = sub.add_parser("talent-find")
    parser_b_find.add_argument("--name", required=True)

    parser_b_upsert = sub.add_parser("talent-upsert")
    parser_b_upsert.add_argument(
        "--json",
        required=True,
        help="Path to JSON containing action=upsert payload.",
    )

    parser_b_bulk = sub.add_parser("talent-bulk-upsert")
    parser_b_bulk.add_argument(
        "--json",
        required=True,
        help="Path to JSON containing a list of talent profiles for batch upsert.",
    )

    parser_export = sub.add_parser("export")
    parser_export.add_argument("--out", required=False, default="")

    return parser


def main() -> None:
    settings = get_settings()
    repo = TalentRepository(db_path=settings.db_path)
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init-db":
        repo.init_db()
        _print_json({"ok": True, "db_path": str(settings.db_path)})
        return

    if args.command == "arxiv-daily-authors":
        _log_step("Initializing database")
        repo.init_db()
        categories = [item.strip() for item in args.categories.split(",") if item.strip()]
        payload = {"date": args.date, "categories": categories}
        _log_step("Starting daily arXiv paper collection")
        result = run_arxiv_robotics_daily_collector(
            payload=payload,
            arxiv_client=ArxivClient(
                timeout_seconds=settings.http_timeout_seconds,
                max_results=settings.arxiv_max_results,
                local_timezone=settings.arxiv_local_timezone,
            ),
            html_parser=ArxivHtmlParser(timeout_seconds=settings.http_timeout_seconds),
            repo=repo,
            persist_mentions=args.persist_mentions,
            progress_cb=_log_step,
        )
        _log_step("Writing output")
        _write_json_output(result, args.out_json)
        return

    if args.command == "talent-find":
        repo.init_db()
        payload = {"action": "find", "name": args.name}
        result = run_talent_database_sync(payload=payload, repo=repo)
        _print_json(result, indent=2)
        return

    if args.command == "talent-upsert":
        repo.init_db()
        payload_path = Path(args.json)
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        result = run_talent_database_sync(payload=payload, repo=repo)
        _print_json(result, indent=2)
        return

    if args.command == "talent-bulk-upsert":
        repo.init_db()
        payload_path = Path(args.json)
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        result = run_talent_database_bulk_upsert(payload=payload, repo=repo)
        _print_json(result, indent=2)
        return

    if args.command == "export":
        repo.init_db()
        exporter = ExportService(repo=repo)
        output = _resolve_export_output(explicit_out=args.out, export_dir=settings.export_dir)
        path = exporter.export_flat_csv(output)
        _print_json({"ok": True, "output": str(path)})
        return

    raise RuntimeError(f"Unsupported command: {args.command}")


def _write_json_output(payload: dict, out_json: str) -> None:
    if out_json:
        out_path = Path(out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    _print_json(payload, indent=2)


def _print_json(payload: dict, indent: int | None = None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=indent)
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def _log_step(message: str) -> None:
    print(f"[arxiv-daily-authors] {message}", file=sys.stderr, flush=True)


def _resolve_export_output(explicit_out: str, export_dir: Path) -> Path:
    if explicit_out:
        return Path(explicit_out)
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir / "talents.csv"


if __name__ == "__main__":
    main()
