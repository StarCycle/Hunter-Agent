from __future__ import annotations

import re
from datetime import date, datetime


def parse_iso_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


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


def split_other_category(raw_category: str) -> tuple[str, str | None]:
    token = (raw_category or "").strip()
    if token.startswith("其它:"):
        detail = token.split(":", 1)[1].strip()
        return "其它", detail or None
    return token, None
