from __future__ import annotations

import csv
from pathlib import Path

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
                    "name": "",
                    "education": "",
                    "institution": "",
                    "position": "",
                    "grade_or_years": "",
                    "city": "",
                    "country": "",
                    "graduation_time": "",
                    "research_fields": "",
                    "homepage_url": "",
                    "resume_pdf": "",
                    "source_links": "",
                    "evidence_summary": "",
                    "notes": "",
                    "created_at": "",
                    "updated_at": "",
                    "wechat": "",
                    "phone": "",
                    "email": "",
                    "project_categories": "",
                }
            ]
        with output_path.open("w", encoding="utf-8-sig", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return output_path
