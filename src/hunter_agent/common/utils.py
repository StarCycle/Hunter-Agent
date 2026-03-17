from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Iterator

from hunter_agent.common.enums import LEGACY_PROJECT_CATEGORY_ALIASES, PROJECT_CATEGORIES


def parse_iso_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def iter_date_range(start_date: date, end_date: date) -> Iterator[date]:
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def previous_calendar_week_range(anchor_date: date | None = None) -> tuple[date, date]:
    current = anchor_date or date.today()
    current_week_start = current - timedelta(days=current.weekday())
    previous_week_start = current_week_start - timedelta(days=7)
    previous_week_end = previous_week_start + timedelta(days=6)
    return previous_week_start, previous_week_end


def normalize_name(value: str) -> str:
    collapsed = re.sub(r"\s+", "", value or "")
    return collapsed.strip().lower()


def normalize_email(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip().lower()


def normalize_phone(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"[^\d+]", "", value)


def normalize_project_category(raw_category: str) -> str:
    token = (raw_category or "").strip()
    if not token:
        raise ValueError("Project category cannot be empty.")

    if token in PROJECT_CATEGORIES:
        return token

    if token in LEGACY_PROJECT_CATEGORY_ALIASES:
        normalized = LEGACY_PROJECT_CATEGORY_ALIASES[token]
        if normalized == "other":
            raise ValueError("Use 'other:<text>' instead of bare 'other'.")
        return normalized

    if token.startswith("other:"):
        detail = token.split(":", 1)[1].strip()
        if not detail:
            raise ValueError("Category 'other' requires non-empty detail.")
        return f"other:{detail}"

    if token.startswith("鍏朵粬:") or token.startswith("\u5176\u4ed6:"):
        detail = token.split(":", 1)[1].strip()
        if not detail:
            raise ValueError("Category 'other' requires non-empty detail.")
        return f"other:{detail}"

    raise ValueError(
        f"Unsupported project category: {token}. "
        f"Allowed: {PROJECT_CATEGORIES} or use 'other:<text>'."
    )


def split_other_category(raw_category: str) -> tuple[str, str | None]:
    token = normalize_project_category(raw_category)
    if token.startswith("other:"):
        detail = token.split(":", 1)[1].strip()
        return "other", detail or None
    return token, None
