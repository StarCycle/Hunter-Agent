# Codex Weekly arXiv Workflow

## Purpose

This project helps Codex collect Chinese robotics authors from arXiv, enrich their profiles with public web information, save the results into SQLite, and export the full database to CSV.

## What Codex should do

1. Run `hunter-agent arxiv-range-authors` to collect author candidates from arXiv.
2. If the user does not provide dates, use the default previous calendar week.
3. Review each author candidate and decide whether the author is Chinese.
4. Discard non-Chinese authors immediately. Do not save them.
5. For each remaining author, you may use more than 5 web searches when needed. Prioritize finding a reliable graduation year and current position.
6. Collect as many of these fields as possible:
   - `name`
   - `institution`
   - `position`
   - `city`
   - `country`
   - `graduation_time`
   - `research_fields`
   - `email`
   - `phone`
   - `wechat`
   - `homepage_url`
   - `source_links`
   - `evidence_summary`
   - `notes`
7. If a field cannot be confirmed, leave it empty.
8. Do not invent facts.
9. Use `hunter-agent talent-bulk-upsert --json ...` to write the enriched profiles into SQLite.
10. Use `hunter-agent export --out ...` to export the entire database to CSV.

## Search guidance

- Use recent papers, lab pages, homepages, university profiles, and public contact pages as the main sources.
- For `position`, use one of: `undergraduate`, `masters`, `phd`, `postdoc`, `faculty`, `academia`, `industry`.
- Spend extra search effort on `graduation_time` because it is often missing in weak profiles.
- City and country should reflect the author's current institution when possible.
- `homepage_url` is optional. Try to find it, but do not treat it as a completion requirement.
- `source_links` should include the main URLs used to support the profile.
- `evidence_summary` should briefly explain how the key fields were determined.

## Commands

Initialize the database:

```powershell
hunter-agent init-db
```

Collect candidates for the default previous calendar week:

```powershell
hunter-agent arxiv-range-authors --out-json .\exports\arxiv-author-candidates.json
```

Collect candidates for a specific range:

```powershell
hunter-agent arxiv-range-authors --start-date 2026-03-02 --end-date 2026-03-08 --categories cs.RO --out-json .\exports\arxiv-author-candidates.json
```

Write enriched profiles:

```powershell
hunter-agent talent-bulk-upsert --json .\exports\author-profiles.json
```

Export the full database:

```powershell
hunter-agent export --out .\exports\talents.csv
```

## JSON payload shape

Codex should write a JSON file in this shape:

```json
{
  "profiles": [
    {
      "name": "Author Name",
      "institution": "Current Institution",
      "position": "phd",
      "city": "City",
      "country": "Country",
      "graduation_time": "2024 PhD",
      "research_fields": "robot learning, manipulation",
      "email": "name@example.com",
      "phone": "",
      "wechat": "",
      "homepage_url": "https://example.com",
      "source_links": "https://example.com/profile; https://scholar.google.com/...",
      "evidence_summary": "Institution and city confirmed from lab profile. Research fields derived from homepage and recent papers.",
      "notes": ""
    }
  ]
}
```
