---
name: arxiv-robotics-daily
description: Collect author-affiliation-paper lists from arXiv robotics papers for a given day. Use when OpenClaw needs daily robotics paper authors as upstream candidates.
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
      "author_name": "Author",
      "affiliation": "Institution",
      "paper_title": "Paper Title",
      "arxiv_id": "2603.00001",
      "paper_url": "https://arxiv.org/abs/2603.00001",
      "published_at": "2026-03-01T12:00:00Z"
    }
  ]
}
```

## Notes

- Prefer API author affiliation when available.
- Use arXiv abstract page metadata fallback when affiliation is missing.
