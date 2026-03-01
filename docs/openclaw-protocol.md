# OpenClaw Skill Protocol

This document fixes the JSON contract between OpenClaw and this project.

## Version

- Protocol version: `v1`
- Effective date: `2026-03-01`

## Daily ArXiv Paper Collector: `arxiv-robotics-daily`

Purpose: query one day of arXiv robotics papers and return paper-level records with title, URL, author list, and raw affiliation clues.

### Input Schema

- File: `docs/schemas/arxiv_robotics_daily_input.schema.json`
- Required fields:
  - `date` (`YYYY-MM-DD`)
- Optional fields:
  - `categories` (default: `["cs.RO"]`)

### Output Schema

- File: `docs/schemas/arxiv_robotics_daily_output.schema.json`
- Fields:
  - `date`
  - `records[]`:
    - `paper_title`
    - `paper_url`
    - `authors[]`
    - `affiliation_info` (nullable, raw text snippet from arXiv HTML)

### Runtime Contract

- Skill A may persist `paper` and `paper_author_mention` into SQLite when `persist_mentions=true`.
- `affiliation_info` is extracted from `https://arxiv.org/html/<arxiv_id>` body text.
- `affiliation_info` is intentionally unstructured for downstream LLM parsing in OpenClaw.

## Talent Database Sync: `talent-db-sync`

Purpose: find existing profile by name or upsert profile into SQLite with dedup scoring.

### Input Schema

- File: `docs/schemas/talent_database_sync_input.schema.json`
- `action = "find"`:
  - required: `name`
- `action = "upsert"`:
  - required: `profile` (see `docs/schemas/talent_profile.schema.json`)

### Output Schemas

- Find output: `docs/schemas/talent_database_sync_find_output.schema.json`
- Upsert output: `docs/schemas/talent_database_sync_upsert_output.schema.json`

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
