from __future__ import annotations

import argparse
import json
from pathlib import Path

from hunter_agent.arxiv.client import ArxivClient
from hunter_agent.arxiv.parser import ArxivHtmlParser
from hunter_agent.config import get_settings
from hunter_agent.db.repo import TalentRepository
from hunter_agent.services.export_service import ExportService
from hunter_agent.skills.skill_a_daily_arxiv import run_skill_a
from hunter_agent.skills.skill_b_talent_db import run_skill_b


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hunter-agent")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db")

    parser_a = sub.add_parser("skill-a")
    parser_a.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser_a.add_argument(
        "--categories",
        default="cs.RO",
        help="Comma-separated arXiv categories, e.g. cs.RO,cs.AI",
    )
    parser_a.add_argument(
        "--persist-mentions",
        action="store_true",
        help="Persist author-paper mentions to SQLite.",
    )
    parser_a.add_argument("--out-json", default="", help="Optional output JSON path.")

    parser_b_find = sub.add_parser("skill-b-find")
    parser_b_find.add_argument("--name", required=True)

    parser_b_upsert = sub.add_parser("skill-b-upsert")
    parser_b_upsert.add_argument(
        "--json",
        required=True,
        help="Path to JSON containing action=upsert payload.",
    )

    parser_export = sub.add_parser("export")
    parser_export.add_argument("--format", choices=["csv", "xlsx"], default="xlsx")
    parser_export.add_argument("--out", required=False, default="")

    return parser


def main() -> None:
    settings = get_settings()
    repo = TalentRepository(db_path=settings.db_path)
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init-db":
        repo.init_db()
        print(json.dumps({"ok": True, "db_path": str(settings.db_path)}, ensure_ascii=False))
        return

    if args.command == "skill-a":
        repo.init_db()
        categories = [item.strip() for item in args.categories.split(",") if item.strip()]
        payload = {"date": args.date, "categories": categories}
        result = run_skill_a(
            payload=payload,
            arxiv_client=ArxivClient(
                timeout_seconds=settings.http_timeout_seconds,
                max_results=settings.arxiv_max_results,
            ),
            html_parser=ArxivHtmlParser(timeout_seconds=settings.http_timeout_seconds),
            repo=repo,
            persist_mentions=args.persist_mentions,
        )
        _write_json_output(result, args.out_json)
        return

    if args.command == "skill-b-find":
        repo.init_db()
        payload = {"action": "find", "name": args.name}
        result = run_skill_b(payload=payload, repo=repo)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "skill-b-upsert":
        repo.init_db()
        payload_path = Path(args.json)
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        result = run_skill_b(payload=payload, repo=repo)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "export":
        repo.init_db()
        exporter = ExportService(repo=repo)
        output = _resolve_export_output(
            fmt=args.format, explicit_out=args.out, export_dir=settings.export_dir
        )
        if args.format == "csv":
            path = exporter.export_flat_csv(output)
        else:
            path = exporter.export_xlsx(output)
        print(json.dumps({"ok": True, "output": str(path)}, ensure_ascii=False))
        return

    raise RuntimeError(f"Unsupported command: {args.command}")


def _write_json_output(payload: dict, out_json: str) -> None:
    if out_json:
        out_path = Path(out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _resolve_export_output(fmt: str, explicit_out: str, export_dir: Path) -> Path:
    if explicit_out:
        return Path(explicit_out)
    export_dir.mkdir(parents=True, exist_ok=True)
    if fmt == "csv":
        return export_dir / "talents.csv"
    return export_dir / "talents.xlsx"


if __name__ == "__main__":
    main()
