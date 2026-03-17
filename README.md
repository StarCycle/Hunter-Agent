# hunter-agent

`hunter-agent` is a small Python CLI for collecting arXiv robotics authors, enriching Chinese author profiles with Codex, storing them in SQLite, and exporting the full database to CSV.

## What Codex is

Codex is an AI assistant that can read project files, run terminal commands, and follow the workflow described in this repository.

## Project flow

1. Collect author candidates from arXiv robotics papers in a date range.
2. Keep only Chinese authors.
3. Use public web information to enrich each author profile.
4. Capture structured profile fields such as institution, position, graduation time, and research fields.
5. Upsert the profiles into SQLite.
6. Export the full database to CSV.

## Install

```powershell
python -m pip install -e .
```

If your environment cannot fetch build dependencies but already has `setuptools`, use:

```powershell
python -m pip install -e . --no-build-isolation
```

## Quick start

Just tell codex:

`read docs/codex_weekly_arxiv_workflow.md and perform the task in the file`

## Common commands

Collect author candidates for the default previous calendar week:

```powershell
hunter-agent arxiv-range-authors --out-json .\exports\arxiv-author-candidates.json
```

Collect author candidates for a specific range:

```powershell
hunter-agent arxiv-range-authors --start-date 2026-03-02 --end-date 2026-03-08 --categories cs.RO --out-json .\exports\arxiv-author-candidates.json
```

Write enriched author profiles into the database:

```powershell
hunter-agent talent-bulk-upsert --json .\examples\sample_author_enrichment_payload.json
```

Export the full database to CSV:

```powershell
hunter-agent export --out .\exports\talents.csv
```

The export CSV omits internal database ids. It includes profile fields such as `name`, `institution`, `position`, `city`, `country`, `graduation_time`, contact fields, and evidence fields.

## Talent profile fields

- `position` supports these values: `undergraduate`, `masters`, `phd`, `postdoc`, `faculty`, `academia`, `industry`
- `graduation_time` should be filled whenever it can be supported by public evidence
- If a field cannot be verified, leave it empty instead of guessing

## Default paths

- Database: `data/hunter.db`
- Export directory: `exports/`

These can be overridden with:

- `HUNTER_DB_PATH`
- `HUNTER_EXPORT_DIR`
- `HUNTER_HTTP_TIMEOUT_SECONDS`
- `HUNTER_ARXIV_LOCAL_TIMEZONE`
