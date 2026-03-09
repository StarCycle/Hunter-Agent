---
name: arxiv-robotics-daily
description: Collect daily arXiv robotics papers with title, url, author list, affiliation_info, and paper_summary for downstream talent mining.
---

# arxiv-robotics-daily

## Execute

Run `scripts/run.py` with JSON input:

```json
{
  "date": "2026-03-01",
  "categories": ["cs.RO"]
}
```

The script returns:

```json
{
  "date": "2026-03-01",
  "records": [
    {
      "paper_title": "Paper Title",
      "paper_url": "https://arxiv.org/abs/2603.00001",
      "authors": ["Author A", "Author B"],
      "affiliation_info": "Raw text extracted from https://arxiv.org/html/<id>",
      "paper_summary": "Abstract text from arXiv API"
    }
  ]
}
```

## Notes

- `affiliation_info` is intentionally unstructured raw text for downstream parsing.
- `paper_summary` should be used for research-domain classification.
- The bundled `scripts/run.py` already ensures SQLite schema initialization (`repo.init_db()`).
- This skill paginates the arXiv feed until no more entries return, so it always attempts to retrieve every paper for the requested day without a hard max-results cap.
## OpenClaw Troubleshooting

- If OpenClaw cannot detect this skill, verify the folder path is `~/.openclaw/workspace/skills/arxiv-robotics-daily`.
- Ensure `SKILL.md` and `scripts/run.py` both exist and the skill folder name matches `name: arxiv-robotics-daily`.
- If changes are not picked up, start a new session or restart ClawX/OpenClaw so skill metadata is reloaded.
