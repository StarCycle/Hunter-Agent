---
name: talent-db-sync
description: Find, upsert, and export embodied AI talent records in SQLite.
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
    "project_categories": ["Manipulation算法", "机器人底层控制和软件", "其他:灵巧手"],
    "education": "Master",
    "institution": "Example University",
    "grade_or_years": "3 years",
    "resume_pdf": "https://example.com/resume.pdf",
    "notes": "Source: arXiv + web search"
  }
}
```

Export full talent DB to CSV:

```json
{
  "action": "export",
  "out_csv": "exports/talents.csv"
}
```

## `project_categories` Allowed Values

One profile can have multiple categories. Use zero to many entries in `project_categories`.

- `Manipulation算法`
- `足式运动控制`
- `动力学仿真`
- `机械结构设计`
- `嵌入式软硬件`
- `机器人底层控制和软件`
- `硬件产品外观设计`
- `具身产品运营和市场开发`
- `其他:<自定义方向>`

## Notes

- Contact values are normalized for deduplication.
- If `project_categories` is non-empty, existing categories for that talent are replaced.
- `scripts/run.py` bootstraps SQLite (`repo.init_db()`), so no separate `init-db` call is required.
