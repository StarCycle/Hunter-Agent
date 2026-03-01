---
name: talent-db-sync
description: Find and upsert embodied AI talent records in SQLite by person name and profile data. Use when OpenClaw needs candidate deduplication and profile persistence.
---

# talent-db-sync

## Execute

Run `scripts/run.py` with JSON input.

Find by name:

```json
{
  "action": "find",
  "name": "Alice Smith"
}
```

Upsert profile:

```json
{
  "action": "upsert",
  "profile": {
    "name": "Alice Smith",
    "wechat": "alice_robotics",
    "phone": "+86 13800138000",
    "email": "alice@example.com",
    "project_categories": ["Manipulation算法", "其它:柔性抓取"],
    "education": "Master",
    "institution": "Example University",
    "grade_or_years": "3 years",
    "resume_pdf": "https://example.com/resume.pdf"
  }
}
```

## Notes

- Contact values are normalized for deduplication.
- If profile has non-empty `project_categories`, existing categories are replaced.
