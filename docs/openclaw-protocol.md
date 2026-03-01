# OpenClaw Skill Protocol

This document fixes the JSON contract between OpenClaw and this project.

## Version

- Protocol version: `v1`
- Effective date: `2026-03-01`

## Skill A: `arxiv-robotics-daily`

Purpose: query one day of arXiv robotics papers and return `author - affiliation - paper`.

### Input Schema

- File: `docs/schemas/skill_a_input.schema.json`
- Required fields:
  - `date` (`YYYY-MM-DD`)
- Optional fields:
  - `categories` (default: `["cs.RO"]`)

### Output Schema

- File: `docs/schemas/skill_a_output.schema.json`
- Fields:
  - `date`
  - `records[]`:
    - `author_name`
    - `affiliation` (nullable)
    - `paper_title`
    - `arxiv_id`
    - `paper_url`
    - `published_at` (nullable)

### Runtime Contract

- Skill A may persist mentions into SQLite when `persist_mentions=true`.
- arXiv API author affiliation is preferred.
- If affiliation is missing, parser falls back to arXiv HTML meta tags.

## Skill B: `talent-db-sync`

Purpose: find existing profile by name or upsert profile into SQLite with dedup scoring.

### Input Schema

- File: `docs/schemas/skill_b_input.schema.json`
- `action = "find"`:
  - required: `name`
- `action = "upsert"`:
  - required: `profile` (see `docs/schemas/talent_profile.schema.json`)

### Output Schemas

- Find output: `docs/schemas/skill_b_find_output.schema.json`
- Upsert output: `docs/schemas/skill_b_upsert_output.schema.json`

`upsert` includes:

- `profile.operation`: `insert` or `update`
- `profile.dedup`:
  - `candidate_id`
  - `score`
  - `conflict`
  - `reasons[]`
  - `forced_insert` (present when conflict blocks merge)

## Dedup Policy (v1)

- Name matching:
  - exact normalized name: `+40`
  - fuzzy name similarity >= `0.92`: `+35`
  - fuzzy name similarity >= `0.88`: `+30`
  - fuzzy name similarity >= `0.80`: `+15`
- Contact matching (`email/phone/wechat`):
  - exact match: `+60` per field
  - conflict: `-100` and mark hard conflict
- Institution:
  - same institution: `+20`
  - different institution: `-15`
- Merge threshold:
  - merge only if score >= `50` and no hard conflict
  - otherwise create new talent row
