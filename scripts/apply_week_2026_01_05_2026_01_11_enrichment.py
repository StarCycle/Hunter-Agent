from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "hunter.db"
PAYLOAD_PATH = ROOT / "exports" / "author-profiles-2026-01-05_to_2026-01-11-enriched.json"

TARGET_NOTE = "Reviewed one-by-one for week 2026-01-05 to 2026-01-11 before insertion."
NEW_NOTE = "Enriched from public arXiv paper affiliation pages and project/homepage links for week 2026-01-05 to 2026-01-11."


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def normalize_email(email: str) -> str:
    return email.strip().lower()


def clean_profile(profile: dict) -> dict:
    cleaned = dict(profile)

    if cleaned.get("homepage_url") == "https://robosense2025.github.io" and not cleaned.get("institution"):
        cleaned["city"] = ""
        cleaned["country"] = ""
        cleaned["evidence_summary"] = cleaned["evidence_summary"].replace(" city=Navigate Anywhere;", "")
        cleaned["evidence_summary"] = cleaned["evidence_summary"].replace(" country=USA;", "")

    if cleaned.get("city") in {"Navigate Anywhere", "Ltd", "Qing Zhao", "NJ"}:
        cleaned["city"] = ""

    if cleaned.get("institution", "").startswith("University of California, Los Angeles"):
        cleaned["institution"] = "University of California, Los Angeles"
        cleaned["city"] = "Los Angeles"
        cleaned["country"] = "USA"

    if cleaned.get("institution") == "Academy of Artificial Intelligence":
        cleaned["institution"] = "Beijing Academy of Artificial Intelligence"
        cleaned["city"] = "Beijing"
        cleaned["country"] = "China"

    if cleaned.get("institution") == "Research":
        cleaned["institution"] = "Agibot Research"
        cleaned["city"] = "Shanghai"
        cleaned["country"] = "China"

    if cleaned.get("institution", "").endswith(", China"):
        cleaned["institution"] = cleaned["institution"].removesuffix(", China")
        cleaned["country"] = cleaned.get("country") or "China"

    return cleaned


def main() -> None:
    payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
    profiles = [clean_profile(item) for item in payload["profiles"]]
    by_name = {normalize_name(item["name"]): item for item in profiles}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute("DELETE FROM talent WHERE notes = ?", (NEW_NOTE,))

        targets = conn.execute(
            "SELECT id, name, normalized_name FROM talent WHERE notes = ? ORDER BY id",
            (TARGET_NOTE,),
        ).fetchall()

        updated = 0
        emailed = 0
        for row in targets:
            profile = by_name.get(row["normalized_name"])
            if not profile:
                continue

            conn.execute(
                """
                UPDATE talent
                SET institution = ?,
                    position = ?,
                    city = ?,
                    country = ?,
                    graduation_time = ?,
                    research_fields = ?,
                    homepage_url = ?,
                    source_links = ?,
                    evidence_summary = ?,
                    notes = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (
                    profile.get("institution", ""),
                    profile.get("position", ""),
                    profile.get("city", ""),
                    profile.get("country", ""),
                    profile.get("graduation_time", ""),
                    profile.get("research_fields", ""),
                    profile.get("homepage_url", ""),
                    profile.get("source_links", ""),
                    profile.get("evidence_summary", ""),
                    NEW_NOTE,
                    row["id"],
                ),
            )
            updated += 1

            email = (profile.get("email") or "").strip()
            if email:
                conn.execute(
                    """
                    INSERT INTO talent_contact (talent_id, type, value, normalized_value, verified)
                    VALUES (?, 'email', ?, ?, 0)
                    ON CONFLICT(type, normalized_value) DO UPDATE SET
                      talent_id = excluded.talent_id,
                      value = excluded.value,
                      updated_at = datetime('now')
                    """,
                    (row["id"], email, normalize_email(email)),
                )
                emailed += 1

        conn.commit()
        print(f"updated={updated}")
        print(f"emails_upserted={emailed}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
