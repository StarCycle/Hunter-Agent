from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

from hunter_agent.common.schemas import ArxivPaperAffiliationRecord, TalentProfile
from hunter_agent.common.utils import (
    normalize_email,
    normalize_name,
    normalize_phone,
    split_other_category,
)
from hunter_agent.db.sqlite import connect, run_sql_script
from hunter_agent.services.dedup_service import DedupService


class TalentRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.dedup_service = DedupService()

    def init_db(self) -> None:
        migration_file = (
            Path(__file__).resolve().parent / "migrations" / "001_init.sql"
        )
        conn = connect(self.db_path)
        try:
            run_sql_script(conn, migration_file)
            self._ensure_paper_summary_column(conn)
        finally:
            conn.close()

    def _ensure_paper_summary_column(self, conn: sqlite3.Connection) -> None:
        existing = conn.execute("PRAGMA table_info(paper)").fetchall()
        columns = {row["name"] for row in existing}
        if "summary" in columns:
            return
        conn.execute("ALTER TABLE paper ADD COLUMN summary TEXT")
        conn.commit()

    def find_talents_by_name(self, name: str) -> list[dict]:
        normalized = normalize_name(name)
        conn = connect(self.db_path)
        try:
            talents = conn.execute(
                "SELECT * FROM talent WHERE normalized_name = ? ORDER BY updated_at DESC",
                (normalized,),
            ).fetchall()
            return [self._build_talent_view(conn, row["id"]) for row in talents]
        finally:
            conn.close()

    def upsert_talent(self, profile: TalentProfile) -> dict:
        conn = connect(self.db_path)
        try:
            talent_id, dedup = self._resolve_existing_talent(conn, profile)
            operation = "insert"
            if talent_id is None:
                talent_id = self._insert_talent(conn, profile)
            else:
                self._update_talent(conn, talent_id, profile)
                operation = "update"

            self._upsert_contacts(conn, talent_id, profile)
            if profile.project_categories:
                self._replace_project_tags(conn, talent_id, profile.project_categories)
            conn.commit()
            result = self._build_talent_view(conn, talent_id)
            result["dedup"] = dedup
            result["operation"] = operation
            return result
        finally:
            conn.close()

    def save_arxiv_mentions(
        self,
        source_date: str,
        records: list[ArxivPaperAffiliationRecord],
        categories: list[str],
    ) -> int:
        conn = connect(self.db_path)
        try:
            count = 0
            for record in records:
                arxiv_id = _extract_arxiv_id_from_url(record.paper_url)
                if not arxiv_id:
                    continue
                paper_id = self._upsert_paper(
                    conn=conn,
                    arxiv_id=arxiv_id,
                    title=record.paper_title,
                    published_date=None,
                    categories=categories,
                    summary=record.paper_summary,
                )
                for author_name in record.authors:
                    conn.execute(
                        """
                        INSERT INTO paper_author_mention
                        (paper_id, talent_name, normalized_name, affiliation, source_date)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            paper_id,
                            author_name,
                            normalize_name(author_name),
                            None,
                            source_date,
                        ),
                    )
                    count += 1
            conn.commit()
            return count
        finally:
            conn.close()

    def export_flat_rows(self) -> list[dict]:
        conn = connect(self.db_path)
        try:
            rows = conn.execute(
                """
                SELECT
                  t.id AS talent_id,
                  t.name,
                  t.education,
                  t.institution,
                  t.grade_or_years,
                  t.resume_pdf,
                  t.notes,
                  t.created_at,
                  t.updated_at
                FROM talent t
                ORDER BY t.updated_at DESC
                """
            ).fetchall()
            result: list[dict] = []
            for row in rows:
                talent_id = row["talent_id"]
                contacts = conn.execute(
                    """
                    SELECT type, value FROM talent_contact
                    WHERE talent_id = ?
                    ORDER BY type
                    """,
                    (talent_id,),
                ).fetchall()
                tags = conn.execute(
                    """
                    SELECT category, other_text FROM talent_project_tag
                    WHERE talent_id = ?
                    ORDER BY category
                    """,
                    (talent_id,),
                ).fetchall()
                row_dict = dict(row)
                row_dict["wechat"] = _first_contact(contacts, "wechat")
                row_dict["phone"] = _first_contact(contacts, "phone")
                row_dict["email"] = _first_contact(contacts, "email")
                row_dict["project_categories"] = ",".join(
                    [
                        tag["category"]
                        if not tag["other_text"]
                        else f'{tag["category"]}:{tag["other_text"]}'
                        for tag in tags
                    ]
                )
                result.append(row_dict)
            return result
        finally:
            conn.close()

    def export_table_rows(self, table_name: str) -> list[dict]:
        if table_name not in {
            "talent",
            "talent_contact",
            "talent_project_tag",
            "paper",
            "paper_author_mention",
        }:
            raise ValueError(f"Unsupported table: {table_name}")
        conn = connect(self.db_path)
        try:
            rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def _resolve_existing_talent(
        self, conn: sqlite3.Connection, profile: TalentProfile
    ) -> tuple[int | None, dict]:
        candidates = self._collect_dedup_candidates(conn=conn, profile=profile)
        decision = self.dedup_service.choose_candidate(profile=profile, candidates=candidates)
        decision_payload = {
            "candidate_id": decision.candidate_id,
            "score": decision.score,
            "conflict": decision.conflict,
            "reasons": decision.reasons,
        }
        if decision.candidate_id is None:
            return None, decision_payload
        if decision.conflict:
            # Hard conflicts are treated as distinct talents.
            decision_payload["forced_insert"] = True
            return None, decision_payload
        return decision.candidate_id, decision_payload

    def _collect_dedup_candidates(
        self, conn: sqlite3.Connection, profile: TalentProfile
    ) -> list[dict]:
        candidate_ids: set[int] = set()
        normalized_name = normalize_name(profile.name)

        rows = conn.execute(
            "SELECT id FROM talent WHERE normalized_name = ? ORDER BY updated_at DESC",
            (normalized_name,),
        ).fetchall()
        for row in rows:
            candidate_ids.add(int(row["id"]))

        for ctype, value in _contacts_from_profile(profile).items():
            if not value:
                continue
            row = conn.execute(
                """
                SELECT talent_id FROM talent_contact
                WHERE type = ? AND normalized_value = ?
                """,
                (ctype, value),
            ).fetchone()
            if row:
                candidate_ids.add(int(row["talent_id"]))

        if profile.institution:
            inst_rows = conn.execute(
                """
                SELECT id FROM talent
                WHERE institution = ?
                ORDER BY updated_at DESC
                LIMIT 20
                """,
                (profile.institution,),
            ).fetchall()
            for row in inst_rows:
                candidate_ids.add(int(row["id"]))

        # Fuzzy pool: recent talents for near-name matching.
        recent_rows = conn.execute(
            """
            SELECT id FROM talent
            ORDER BY updated_at DESC
            LIMIT 200
            """
        ).fetchall()
        for row in recent_rows:
            candidate_ids.add(int(row["id"]))

        candidates: list[dict] = []
        for talent_id in candidate_ids:
            candidates.append(self._build_talent_view(conn, talent_id))
        return candidates

    def _insert_talentsql(self) -> str:
        return """
        INSERT INTO talent
        (name, normalized_name, education, institution, grade_or_years, resume_pdf, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

    def _insert_talent(self, conn: sqlite3.Connection, profile: TalentProfile) -> int:
        cursor = conn.execute(
            self._insert_talentsql(),
            (
                profile.name,
                normalize_name(profile.name),
                profile.education,
                profile.institution,
                profile.grade_or_years,
                profile.resume_pdf,
                profile.notes,
            ),
        )
        return int(cursor.lastrowid)

    def _update_talent(
        self, conn: sqlite3.Connection, talent_id: int, profile: TalentProfile
    ) -> None:
        current = conn.execute("SELECT * FROM talent WHERE id = ?", (talent_id,)).fetchone()
        if current is None:
            raise ValueError(f"Talent id not found: {talent_id}")

        merged = {
            "name": profile.name or current["name"],
            "normalized_name": normalize_name(profile.name or current["name"]),
            "education": profile.education or current["education"],
            "institution": profile.institution or current["institution"],
            "grade_or_years": profile.grade_or_years or current["grade_or_years"],
            "resume_pdf": profile.resume_pdf or current["resume_pdf"],
            "notes": profile.notes or current["notes"],
        }
        conn.execute(
            """
            UPDATE talent SET
              name = ?,
              normalized_name = ?,
              education = ?,
              institution = ?,
              grade_or_years = ?,
              resume_pdf = ?,
              notes = ?,
              updated_at = datetime('now')
            WHERE id = ?
            """,
            (
                merged["name"],
                merged["normalized_name"],
                merged["education"],
                merged["institution"],
                merged["grade_or_years"],
                merged["resume_pdf"],
                merged["notes"],
                talent_id,
            ),
        )

    def _upsert_contacts(
        self, conn: sqlite3.Connection, talent_id: int, profile: TalentProfile
    ) -> None:
        for ctype, value in _contacts_from_profile(profile).items():
            if not value:
                continue
            conn.execute(
                """
                INSERT INTO talent_contact (talent_id, type, value, normalized_value)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(type, normalized_value) DO UPDATE SET
                  talent_id = excluded.talent_id,
                  value = excluded.value,
                  updated_at = datetime('now')
                """,
                (talent_id, ctype, value, value),
            )

    def _replace_project_tags(
        self, conn: sqlite3.Connection, talent_id: int, categories: list[str]
    ) -> None:
        conn.execute("DELETE FROM talent_project_tag WHERE talent_id = ?", (talent_id,))
        for raw_category in categories:
            category, other_text = split_other_category(raw_category)
            conn.execute(
                """
                INSERT INTO talent_project_tag (talent_id, category, other_text)
                VALUES (?, ?, ?)
                """,
                (talent_id, category, other_text),
            )

    def _upsert_paper(
        self,
        conn: sqlite3.Connection,
        arxiv_id: str,
        title: str,
        published_date: str | None,
        categories: list[str],
        summary: str | None,
    ) -> int:
        conn.execute(
            """
            INSERT INTO paper (arxiv_id, title, published_date, categories_json, summary)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(arxiv_id) DO UPDATE SET
              title = excluded.title,
              published_date = excluded.published_date,
              categories_json = excluded.categories_json,
              summary = excluded.summary,
              updated_at = datetime('now')
            """,
            (
                arxiv_id,
                title,
                published_date,
                json.dumps(categories, ensure_ascii=False),
                summary,
            ),
        )
        row = conn.execute(
            "SELECT id FROM paper WHERE arxiv_id = ?",
            (arxiv_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError("Failed to read upserted paper id.")
        return int(row["id"])

    def _build_talent_view(self, conn: sqlite3.Connection, talent_id: int) -> dict:
        row = conn.execute("SELECT * FROM talent WHERE id = ?", (talent_id,)).fetchone()
        if row is None:
            raise ValueError(f"Talent id not found: {talent_id}")
        contacts = conn.execute(
            """
            SELECT type, value, verified, created_at, updated_at
            FROM talent_contact WHERE talent_id = ? ORDER BY type
            """,
            (talent_id,),
        ).fetchall()
        tags = conn.execute(
            """
            SELECT category, other_text, created_at
            FROM talent_project_tag WHERE talent_id = ? ORDER BY category
            """,
            (talent_id,),
        ).fetchall()
        return {
            "talent": dict(row),
            "contacts": [dict(item) for item in contacts],
            "project_tags": [dict(item) for item in tags],
        }


def _contacts_from_profile(profile: TalentProfile) -> dict[str, str | None]:
    return {
        "wechat": (profile.wechat or "").strip() or None,
        "phone": normalize_phone(profile.phone),
        "email": normalize_email(profile.email),
    }


def _first_contact(contacts: list[sqlite3.Row], ctype: str) -> str | None:
    for row in contacts:
        if row["type"] == ctype:
            return row["value"]
    return None


def _extract_arxiv_id_from_url(url: str) -> str:
    parsed = urlparse(url or "")
    if not parsed.path:
        return ""
    return parsed.path.split("/")[-1].strip()
