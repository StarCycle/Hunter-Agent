# hunter-agent

Minimal runnable skeleton for embodied AI talent discovery:

- Skill A: Query daily arXiv robotics papers and return `author - affiliation - paper`.
- Skill B: Query/upsert talent profiles into SQLite.
- Export: Export database data to CSV or XLSX.

## Quick Start

1. Create virtual environment and install dependencies.
2. Initialize database:
   - `python -m hunter_agent.cli init-db`
3. Run skill A:
   - `python -m hunter_agent.cli skill-a --date 2026-03-01`
4. Find a profile:
   - `python -m hunter_agent.cli skill-b-find --name "Alice Smith"`
5. Upsert a profile:
   - `python -m hunter_agent.cli skill-b-upsert --json .\sample_profile.json`
6. Export:
   - `python -m hunter_agent.cli export --format xlsx --out .\exports\talents.xlsx`

## Tests

- Unit tests:
  - `python -m unittest discover -s tests -v`
- Live arXiv integration test:
  - PowerShell: `$env:RUN_INTEGRATION='1'; python -m unittest tests.test_skill_a_integration -v`
