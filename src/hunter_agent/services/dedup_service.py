from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from hunter_agent.common.schemas import TalentProfile
from hunter_agent.common.utils import normalize_email, normalize_name, normalize_phone


@dataclass
class DedupDecision:
    candidate_id: int | None
    score: int
    conflict: bool
    reasons: list[str]


class DedupService:
    """
    Score-based dedup strategy.

    Merge threshold:
      - score >= 60 and no hard conflict
    """

    MERGE_THRESHOLD = 50

    def choose_candidate(
        self,
        profile: TalentProfile,
        candidates: list[dict],
    ) -> DedupDecision:
        if not candidates:
            return DedupDecision(
                candidate_id=None,
                score=0,
                conflict=False,
                reasons=["no_candidates"],
            )

        scored: list[DedupDecision] = [
            self._score_candidate(profile=profile, candidate=c) for c in candidates
        ]

        non_conflict = [item for item in scored if not item.conflict]
        if non_conflict:
            best_non_conflict = max(non_conflict, key=lambda x: x.score)
            if best_non_conflict.score >= self.MERGE_THRESHOLD:
                return best_non_conflict

        conflict_items = [item for item in scored if item.conflict]
        if conflict_items:
            return max(conflict_items, key=lambda x: x.score)

        best = max(scored, key=lambda x: x.score)
        return DedupDecision(
            candidate_id=None,
            score=best.score,
            conflict=False,
            reasons=best.reasons + ["below_threshold"],
        )

    def _score_candidate(self, profile: TalentProfile, candidate: dict) -> DedupDecision:
        talent = candidate["talent"]
        contacts = candidate.get("contacts", [])
        reasons: list[str] = []
        score = 0
        conflict = False

        profile_name = normalize_name(profile.name)
        candidate_name = talent.get("normalized_name", normalize_name(talent["name"]))
        similarity = SequenceMatcher(a=profile_name, b=candidate_name).ratio()
        if profile_name == candidate_name:
            score += 40
            reasons.append("exact_name:+40")
        elif similarity >= 0.92:
            score += 35
            reasons.append(f"fuzzy_name_strong({similarity:.2f}):+35")
        elif similarity >= 0.88:
            score += 30
            reasons.append(f"fuzzy_name_medium({similarity:.2f}):+30")
        elif similarity >= 0.80:
            score += 15
            reasons.append(f"weak_fuzzy_name({similarity:.2f}):+15")

        candidate_contacts = self._contact_map(contacts)
        email = normalize_email(profile.email)
        phone = normalize_phone(profile.phone)
        wechat = (profile.wechat or "").strip() or None

        score_delta, conflict_delta, reason_delta = self._score_contact_field(
            "email", email, candidate_contacts.get("email")
        )
        score += score_delta
        conflict = conflict or conflict_delta
        reasons.extend(reason_delta)

        score_delta, conflict_delta, reason_delta = self._score_contact_field(
            "phone", phone, candidate_contacts.get("phone")
        )
        score += score_delta
        conflict = conflict or conflict_delta
        reasons.extend(reason_delta)

        score_delta, conflict_delta, reason_delta = self._score_contact_field(
            "wechat", wechat, candidate_contacts.get("wechat")
        )
        score += score_delta
        conflict = conflict or conflict_delta
        reasons.extend(reason_delta)

        profile_inst = (profile.institution or "").strip().lower() or None
        candidate_inst = (talent.get("institution") or "").strip().lower() or None
        if profile_inst and candidate_inst:
            if profile_inst == candidate_inst:
                score += 20
                reasons.append("same_institution:+20")
            else:
                score -= 15
                reasons.append("different_institution:-15")

        return DedupDecision(
            candidate_id=int(talent["id"]),
            score=score,
            conflict=conflict,
            reasons=reasons,
        )

    def _score_contact_field(
        self,
        field_name: str,
        profile_value: str | None,
        candidate_value: str | None,
    ) -> tuple[int, bool, list[str]]:
        reasons: list[str] = []
        if not profile_value or not candidate_value:
            return 0, False, reasons
        if profile_value == candidate_value:
            reasons.append(f"same_{field_name}:+60")
            return 60, False, reasons
        reasons.append(f"conflict_{field_name}:-100")
        return -100, True, reasons

    @staticmethod
    def _contact_map(contacts: list[dict]) -> dict[str, str]:
        result: dict[str, str] = {}
        for item in contacts:
            ctype = item.get("type")
            value = item.get("value")
            if ctype and value:
                result[ctype] = value
        return result
