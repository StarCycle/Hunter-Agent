from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook

from hunter_agent.db.repo import TalentRepository


class ExportService:
    def __init__(self, repo: TalentRepository) -> None:
        self.repo = repo

    def export_flat_csv(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rows = self.repo.export_flat_rows()
        if not rows:
            rows = [
                {
                    "talent_id": "",
                    "name": "",
                    "wechat": "",
                    "phone": "",
                    "email": "",
                    "project_categories": "",
                    "education": "",
                    "institution": "",
                    "grade_or_years": "",
                    "resume_pdf": "",
                    "notes": "",
                    "created_at": "",
                    "updated_at": "",
                }
            ]
        with output_path.open("w", encoding="utf-8-sig", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return output_path

    def export_xlsx(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        wb = Workbook()
        wb.remove(wb.active)
        self._write_sheet(wb, "talent_flat", self.repo.export_flat_rows())
        self._write_sheet(wb, "talent", self.repo.export_table_rows("talent"))
        self._write_sheet(
            wb, "talent_contact", self.repo.export_table_rows("talent_contact")
        )
        self._write_sheet(
            wb, "talent_project_tag", self.repo.export_table_rows("talent_project_tag")
        )
        self._write_sheet(wb, "paper", self.repo.export_table_rows("paper"))
        self._write_sheet(
            wb,
            "paper_author_mention",
            self.repo.export_table_rows("paper_author_mention"),
        )
        wb.save(output_path)
        return output_path

    def _write_sheet(self, wb: Workbook, sheet_name: str, rows: list[dict]) -> None:
        ws = wb.create_sheet(title=sheet_name)
        if not rows:
            ws.append(["empty"])
            ws.append([""])
            return
        headers = list(rows[0].keys())
        ws.append(headers)
        for row in rows:
            ws.append([row.get(header) for header in headers])
