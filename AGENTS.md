# Hunter-Agent For Codex

## Preferred Interface

- Use the `hunter-agent` CLI for normal operations.
- Use `python -m hunter_agent.cli ...` only when the console script is not installed yet.
- Avoid calling internal Python functions directly unless debugging tests.

## Default Paths

- SQLite database: `data/hunter.db`
- Export directory: `exports/`
- Sample payloads: `examples/sample_profile.json`, `examples/sample_bulk_profiles.json`

## Environment Variables

- `HUNTER_DB_PATH`
- `HUNTER_EXPORT_DIR`
- `HUNTER_HTTP_TIMEOUT_SECONDS`
- `HUNTER_ARXIV_LOCAL_TIMEZONE`

## Standard Workflows

### 1. Fetch arXiv papers for one day

```powershell
hunter-agent init-db
hunter-agent arxiv-daily-authors --date 2026-03-07 --categories cs.RO --out-json .\exports\papers-2026-03-07.json
```

Add `--persist-mentions` if paper-author mentions should be written into SQLite.

### 2. Upsert talent records and export CSV

```powershell
hunter-agent talent-upsert --json .\examples\sample_profile.json
hunter-agent talent-bulk-upsert --json .\examples\sample_bulk_profiles.json
hunter-agent export --out .\exports\talents.csv
```

## Data Conventions

- `project_categories` uses English slug values.
- Use `other:<text>` for custom categories.
- Legacy garbled labels and prior Chinese labels are accepted and normalized automatically.

## Notes

- arXiv collection is date-based and timezone-aware.
- CLI output is JSON so it can be parsed by Codex or scripts.
- The internal `src/hunter_agent/skills` package is implementation detail, not an external skill system.
