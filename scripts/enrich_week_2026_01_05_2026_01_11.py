from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "hunter.db"
CANDIDATE_PATH = ROOT / "exports" / "arxiv-week-2026-01-05_2026-01-11.json"
OUT_PATH = ROOT / "exports" / "author-profiles-2026-01-05_to_2026-01-11-enriched.json"

TARGET_NOTE = "Reviewed one-by-one for week 2026-01-05 to 2026-01-11 before insertion."
NEW_NOTE = "Enriched from public arXiv paper affiliation pages and project/homepage links for week 2026-01-05 to 2026-01-11."

INSTITUTION_KEYWORDS = (
    "university",
    "institute",
    "school",
    "college",
    "laboratory",
    "laboratories",
    "lab",
    "academy",
    "department",
    "center",
    "centre",
    "research",
    "hospital",
    "clinic",
    "company",
    "co., ltd",
    "co.,ltd",
    "corp",
    "corporation",
    "inc",
    "ltd",
    "robotics",
    "technology",
    "technologies",
    "intelligence",
)

COMPANY_KEYWORDS = (
    "co., ltd",
    "co.,ltd",
    "company",
    "corp",
    "corporation",
    "inc",
    "ltd",
    "robotics technology",
    "technologies",
    "meta ai",
    "nvidia",
    "agibot",
    "engineai",
    "bytedance",
    "xiaomi",
    "huawei",
    "baidu",
    "alibaba",
    "tencent",
)

COUNTRY_PATTERNS = [
    ("Hong Kong SAR, China", ("Hong Kong", "China")),
    ("Macau SAR, China", ("Macau", "China")),
    ("United States of America", (None, "USA")),
    ("United States", (None, "USA")),
    ("USA", (None, "USA")),
    ("U.S.A.", (None, "USA")),
    ("UK", (None, "UK")),
    ("United Kingdom", (None, "UK")),
    ("China", (None, "China")),
    ("Singapore", ("Singapore", "Singapore")),
    ("Australia", (None, "Australia")),
    ("Canada", (None, "Canada")),
    ("Switzerland", (None, "Switzerland")),
    ("Germany", (None, "Germany")),
    ("France", (None, "France")),
    ("Ireland", (None, "Ireland")),
    ("Sweden", (None, "Sweden")),
    ("Austria", (None, "Austria")),
    ("Japan", (None, "Japan")),
    ("Korea", (None, "South Korea")),
    ("South Korea", (None, "South Korea")),
    ("Taiwan", (None, "Taiwan")),
]

CITY_HINTS = (
    "Beijing",
    "Shanghai",
    "Shenzhen",
    "Hangzhou",
    "Xi'an",
    "Xi’an",
    "Urumqi",
    "Singapore",
    "Sydney",
    "Cambridge",
    "Oxford",
    "Hong Kong",
    "Guangzhou",
    "Stockholm",
    "Zurich",
    "Zürich",
    "Dublin",
    "Rochester",
    "Kansas City",
    "Newcastle",
    "Stony Brook",
    "Ithaca",
    "Providence",
    "Brown University",
)

INSTITUTION_LOCATION_HINTS = [
    ("University of Oxford", ("Oxford", "UK")),
    ("University of Cambridge", ("Cambridge", "UK")),
    ("University of Delaware", ("Newark", "USA")),
    ("University of California, Los Angeles", ("Los Angeles", "USA")),
    ("Stanford University", ("Stanford", "USA")),
    ("Brown University", ("Providence", "USA")),
    ("Cornell University", ("Ithaca", "USA")),
    ("Massachusetts Institute of Technology", ("Cambridge", "USA")),
    ("Peking University", ("Beijing", "China")),
    ("Beijing Academy of Artificial Intelligence", ("Beijing", "China")),
    ("Shanghai Innovation Institute", ("Shanghai", "China")),
    ("Agibot Research", ("Shanghai", "China")),
    ("National University of Singapore", ("Singapore", "Singapore")),
    ("ETH Zürich", ("Zurich", "Switzerland")),
]

FIELD_KEYWORDS = [
    (("vision-language-action", "vla"), "vision-language-action, embodied AI"),
    (("manipulation", "grasp", "gripper"), "robot manipulation"),
    (("navigation", "navigate", "vln"), "robot navigation"),
    (("locomotion", "quadruped", "biped", "humanoid"), "robot locomotion"),
    (("autonomous driving", "trajectory forecasting", "occupancy"), "autonomous driving"),
    (("event", "visual-inertial", "slam", "gaussian splatting"), "robot perception"),
    (("world model", "video model"), "world models, embodied AI"),
    (("reinforcement learning", "mppi", "policy"), "reinforcement learning"),
    (("medical", "endoscopic", "mri"), "medical robotics"),
    (("audio-visual", "multimodal"), "multimodal learning"),
    (("uav", "drone"), "aerial robotics"),
]


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    cleaned = text.replace("\n", " ")
    cleaned = cleaned.replace("\u2217", " ")
    cleaned = cleaned.replace("∗", " ")
    cleaned = cleaned.replace("†", " ")
    cleaned = cleaned.replace("‡", " ")
    cleaned = cleaned.replace("•", " ")
    cleaned = cleaned.replace("，", ", ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def extract_urls(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)>,;]+", text)
    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        url = url.rstrip(".,)")
        if url in seen:
            continue
        seen.add(url)
        deduped.append(url)
    return deduped


def extract_emails(text: str) -> list[str]:
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    for locals_blob, domain in re.findall(r"\{([^}]+)\}@([A-Za-z0-9.-]+\.[A-Za-z]{2,})", text):
        for local in locals_blob.split(","):
            local = local.strip()
            if local:
                emails.append(f"{local}@{domain}")
    deduped: list[str] = []
    seen: set[str] = set()
    for email in emails:
        lowered = email.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(lowered)
    return deduped


def candidate_institution_starts(text: str) -> list[tuple[int, str]]:
    matches = list(re.finditer(r"(?<!\S)(\d{1,2})\s+", text))
    starts: list[tuple[int, str]] = []
    starter = re.compile(
        r"^(School|Department|College|Institute|Laboratory|Lab|Academy|Hospital|Clinic|Center|Centre|Research|University|[A-Z][A-Za-z&\-.,' ]{0,80}(University|Institute|College|Academy|Laboratory|Lab|Company|Co\., Ltd|Research|Technology))",
        flags=re.IGNORECASE,
    )
    for match in matches:
        start = match.start()
        snippet = text[match.end() : match.end() + 120].lstrip()
        if starter.search(snippet):
            starts.append((start, match.group(1)))
    return starts


def parse_numbered_affiliations(text: str) -> dict[str, str]:
    starts = candidate_institution_starts(text)
    if not starts:
        return {}
    mapping: dict[str, str] = {}
    for idx, (start, key) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(text)
        segment = text[start:end].strip()
        segment = re.sub(rf"^{re.escape(key)}\s+", "", segment).strip(" ,.;")
        if segment:
            mapping[key] = segment
    return mapping


def extract_author_affiliation_numbers(text: str, author_name: str) -> list[str]:
    match = re.search(re.escape(author_name), text, flags=re.IGNORECASE)
    if not match:
        return []
    suffix = text[match.end() :]
    allowed = set("0123456789, *†‡∗{}^_")
    captured: list[str] = []
    started = False
    for char in suffix:
        if char in allowed:
            captured.append(char)
            if char.isdigit():
                started = True
            continue
        if char.isspace() and not started:
            captured.append(char)
            continue
        break
    return re.findall(r"\d{1,2}", "".join(captured))


def extract_direct_author_clause(text: str, author_name: str) -> str:
    direct_patterns = [
        rf"{re.escape(author_name)}\s+is\s+with\s+([^.;]+)",
        rf"{re.escape(author_name)}\s+are\s+with\s+([^.;]+)",
        rf"{re.escape(author_name)}\s+is\s+from\s+([^.;]+)",
        rf"{re.escape(author_name)}\s+is\s+at\s+([^.;]+)",
        rf"{re.escape(author_name)}[^.;]{{0,24}}(School of[^.;]+)",
        rf"{re.escape(author_name)}[^.;]{{0,24}}(Department of[^.;]+)",
        rf"{re.escape(author_name)}[^.;]{{0,24}}(College of[^.;]+)",
        rf"{re.escape(author_name)}[^.;]{{0,24}}(Institute of[^.;]+)",
        rf"{re.escape(author_name)}[^.;]{{0,24}}([A-Z][^.;]+(?:University|Institute|College|School|Laboratory|Lab|Academy|Company|Co\., Ltd)[^.;]*)",
        rf"{re.escape(author_name)}\s+and\s+[^.]+?\s+are\s+with\s+([^.;]+)",
        rf"All authors are with\s+([^.;]+)",
    ]
    for raw_pattern in direct_patterns:
        match = re.search(raw_pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" ,.;")
    return ""


def sanitize_institution(text: str) -> str:
    cleaned = text.strip(" ,.;")
    protected_patterns = [
        r"ENGINEAI Robotics Technology Co\., Ltd",
        r"Agibot Research",
        r"Beijing Academy of Artificial Intelligence",
        r"University of California, Los Angeles",
        r"University of Delaware[^.;]*",
    ]
    for pattern in protected_patterns:
        match = re.search(pattern, cleaned)
        if match:
            cleaned = match.group(0)
            break
    for marker in ("Email:", "Corresponding author", "Equal contribution", "Project website:", "Homepage:", "Submitted Date:", "Work done as"):
        if marker in cleaned:
            cleaned = cleaned.split(marker, 1)[0].strip(" ,.;")
    cleaned = re.sub(r"\{[^}]+\}@\S+", "", cleaned).strip(" ,.;")
    cleaned = cleaned.replace("♡", "").strip(" ,.;")
    starts = [
        cleaned.find("School of"),
        cleaned.find("Department of"),
        cleaned.find("College of"),
        cleaned.find("Institute of"),
        cleaned.find("Laboratory"),
        cleaned.find("Lab"),
        cleaned.find("Academy"),
        cleaned.find("University"),
    ]
    starts = [value for value in starts if value >= 0]
    if starts:
        cleaned = cleaned[min(starts) :].strip(" ,.;")
    return cleaned


def extract_institution_phrases(text: str) -> list[str]:
    patterns = [
        r"(School of[^.;]+(?:University|Institute|College|Academy|Laboratory|Lab|Company|Co\., Ltd)[^.;]*)",
        r"(Department of[^.;]+(?:University|Institute|College|Academy|Laboratory|Lab|Company|Co\., Ltd)[^.;]*)",
        r"(College of[^.;]+(?:University|Institute|College|Academy|Laboratory|Lab|Company|Co\., Ltd)[^.;]*)",
        r"([A-Z][A-Za-z&\-.,' ]+(?:University|Institute|College|Academy|Laboratory|Lab|Company|Co\., Ltd)[^.;]*)",
    ]
    phrases: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, text):
            phrase = match.strip(" ,.;")
            lowered = phrase.lower()
            if any(keyword in lowered for keyword in INSTITUTION_KEYWORDS):
                phrases.append(sanitize_institution(phrase))
    return list(dict.fromkeys(phrases))


def choose_institution(author_name: str, texts: list[str]) -> str:
    for text in texts:
        numbered = parse_numbered_affiliations(text)
        numbers = extract_author_affiliation_numbers(text, author_name)
        hits = [sanitize_institution(numbered[n]) for n in numbers if n in numbered]
        if hits:
            return " / ".join(dict.fromkeys(hit.strip() for hit in hits if hit.strip()))

    for text in texts:
        clause = extract_direct_author_clause(text, author_name)
        if clause and any(keyword in clause.lower() for keyword in INSTITUTION_KEYWORDS):
            return sanitize_institution(clause)

    institution_candidates: list[str] = []
    for text in texts:
        numbered = parse_numbered_affiliations(text)
        institution_candidates.extend(numbered.values())
        institution_candidates.extend(extract_institution_phrases(text))
    if len(set(institution_candidates)) == 1:
        return institution_candidates[0]
    return ""


def parse_city_country(institution: str, raw_text: str) -> tuple[str, str]:
    combined = institution.strip() if institution else raw_text.strip()
    city = ""
    country = ""
    lowered = combined.lower()
    for inst_hint, inst_location in INSTITUTION_LOCATION_HINTS:
        if inst_hint.lower() in lowered:
            city = city or inst_location[0]
            country = country or inst_location[1]
            break
    for pattern, defaults in COUNTRY_PATTERNS:
        if pattern.lower() in lowered:
            if defaults[0]:
                city = defaults[0]
            country = defaults[1]
            break

    for hint in CITY_HINTS:
        if hint.lower() in lowered:
            city = "Zurich" if hint == "Zürich" else hint
            if city == "Brown University":
                city = "Providence"
            break

    parts = [part.strip() for part in re.split(r"[,;]", combined) if part.strip()]
    if country and parts:
        for idx, part in enumerate(parts):
            if country.lower() in part.lower():
                if idx > 0 and not city:
                    prev = re.sub(r"\b\d{4,6}\b", "", parts[idx - 1]).strip()
                    if prev and len(prev.split()) <= 4 and not any(keyword in prev.lower() for keyword in COMPANY_KEYWORDS):
                        city = prev
                break
    if not country and city in {"Beijing", "Shanghai", "Shenzhen", "Hangzhou", "Xi'an", "Xi’an", "Urumqi", "Guangzhou", "Hong Kong"}:
        country = "China"
    return city, country


def choose_email(author_name: str, emails: list[str]) -> str:
    if not emails:
        return ""
    normalized = normalize_name(author_name)
    for email in emails:
        local = email.split("@", 1)[0]
        if normalized in normalize_name(local) or normalize_name(local) in normalized:
            return email
    return ""


def infer_position(institution: str, text: str, current_position: str | None) -> str:
    lowered = f"{institution} {text}".lower()
    if "undergraduate" in lowered or "bachelor" in lowered:
        return "undergraduate"
    if "master" in lowered:
        return "masters"
    if "phd" in lowered or "doctoral" in lowered:
        return "phd"
    if "postdoc" in lowered:
        return "postdoc"
    if "professor" in lowered:
        return "faculty"
    if any(keyword in lowered for keyword in COMPANY_KEYWORDS):
        return "industry"
    if institution:
        return "academia" if any(k in institution.lower() for k in INSTITUTION_KEYWORDS) else (current_position or "academia")
    return current_position or "academia"


def infer_research_fields(titles: list[str], summaries: list[str]) -> str:
    corpus = " ".join(titles + summaries).lower()
    fields: list[str] = []
    for keywords, label in FIELD_KEYWORDS:
        if any(keyword in corpus for keyword in keywords):
            fields.append(label)
    if not fields:
        return ""
    return ", ".join(dict.fromkeys(fields))


def select_homepage(urls: list[str]) -> str:
    for url in urls:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if "arxiv.org" in host:
            continue
        return url
    return ""


def make_source_links(paper_urls: list[str], urls: list[str]) -> str:
    merged: list[str] = []
    seen: set[str] = set()
    for url in paper_urls + urls:
        if not url or url in seen:
            continue
        seen.add(url)
        merged.append(url)
    return "; ".join(merged)


def build_evidence_summary(
    paper_titles: list[str],
    institution: str,
    city: str,
    country: str,
    email: str,
    homepage_url: str,
) -> str:
    title_part = f"Public arXiv paper affiliation text reviewed for: {paper_titles[0]}." if paper_titles else "Public arXiv paper affiliation text reviewed."
    facts: list[str] = []
    if institution:
        facts.append(f"institution={institution}")
    if city:
        facts.append(f"city={city}")
    if country:
        facts.append(f"country={country}")
    if email:
        facts.append(f"email={email}")
    if homepage_url:
        facts.append("homepage/project URL found")
    if not facts:
        facts.append("no stable personal fields could be confirmed beyond the paper clue")
    return f"{title_part} " + "; ".join(facts) + "."


def load_targets() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
              name,
              institution,
              position,
              city,
              country,
              graduation_time,
              research_fields,
              homepage_url,
              source_links,
              evidence_summary,
              notes
            FROM talent
            WHERE notes = ?
            ORDER BY name
            """,
            (TARGET_NOTE,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def load_candidates() -> dict[str, dict]:
    data = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    return {normalize_name(item["author_name"]): item for item in data["authors"]}


def main() -> None:
    targets = load_targets()
    candidates = load_candidates()
    profiles: list[dict] = []
    missing_candidates: list[str] = []
    enriched_institutions = 0

    for row in targets:
        key = normalize_name(row["name"])
        candidate = candidates.get(key)
        if not candidate:
            missing_candidates.append(row["name"])
            continue

        paper_urls = [paper["paper_url"] for paper in candidate["papers"] if paper.get("paper_url")]
        titles = [paper["paper_title"] for paper in candidate["papers"] if paper.get("paper_title")]
        summaries = [clean_text(paper.get("paper_summary")) for paper in candidate["papers"] if paper.get("paper_summary")]
        texts = [clean_text(paper.get("affiliation_info")) for paper in candidate["papers"] if paper.get("affiliation_info")]
        texts.extend(clean_text(item) for item in candidate.get("affiliation_clues", []) if item)

        urls: list[str] = []
        emails: list[str] = []
        for text in texts:
            urls.extend(extract_urls(text))
            emails.extend(extract_emails(text))
        urls = list(dict.fromkeys(urls))
        emails = list(dict.fromkeys(emails))

        institution = choose_institution(row["name"], texts)
        city, country = parse_city_country(institution, " ".join(texts))
        homepage_url = select_homepage(urls)
        email = choose_email(row["name"], emails)
        position = infer_position(institution, " ".join(texts), row.get("position"))
        research_fields = infer_research_fields(titles, summaries)
        source_links = make_source_links(paper_urls, urls)
        evidence_summary = build_evidence_summary(
            paper_titles=titles,
            institution=institution,
            city=city,
            country=country,
            email=email,
            homepage_url=homepage_url,
        )

        if institution:
            enriched_institutions += 1

        profiles.append(
            {
                "name": row["name"],
                "institution": institution,
                "position": position,
                "city": city,
                "country": country,
                "graduation_time": row.get("graduation_time") or "",
                "research_fields": research_fields,
                "email": email,
                "phone": "",
                "wechat": "",
                "homepage_url": homepage_url,
                "source_links": source_links,
                "evidence_summary": evidence_summary,
                "notes": NEW_NOTE,
            }
        )

    payload = {"profiles": profiles}
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"targets={len(targets)}")
    print(f"profiles={len(profiles)}")
    print(f"institutions_filled={enriched_institutions}")
    print(f"missing_candidates={len(missing_candidates)}")
    if missing_candidates:
        print("missing_sample=" + ", ".join(missing_candidates[:10]))

    field_counts = Counter()
    for profile in profiles:
        for field in ("institution", "city", "country", "research_fields", "email", "homepage_url"):
            if profile.get(field):
                field_counts[field] += 1
    print(json.dumps(field_counts, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
