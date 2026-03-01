---
name: arxiv-robotics-daily
description: Collect daily arXiv robotics papers with title, url, author list, and raw affiliation_info extracted from arXiv HTML pages. Use when OpenClaw needs paper-level author context for downstream talent mining.
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
      "affiliation_info": "Raw text extracted from https://arxiv.org/html/<id>, usually containing title/author block and possible institution clues."
    }
  ]
}
```

## Notes

- `affiliation_info` is intentionally unstructured raw text for LLM parsing downstream.
- Keep output paper-level to reduce token usage.
