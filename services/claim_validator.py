"""
Claim Validator Service
File: services/claim_validator.py

Validates generated Statements of Purpose and application drafts against
confirmed student profile facts and verified program evidence.
Flags or redacts unsupported claims, imaginary publications, fabricated metrics,
and unverified faculty relationships.
"""
from __future__ import annotations

import re
from typing import List, Dict, Any, Tuple
from models.schemas import StudentProfile, Opportunity

class ClaimValidator:
    """Audits draft texts to ensure evidence grounding and zero hallucination."""

    # Patterns for potential hallucinations
    METRIC_PATTERN = re.compile(r"\b(\d{1,2}(?:\.\d+)?%|\b\d{2,3}%\s+accuracy|\bprecision of \d+|\bAUC\b)", re.IGNORECASE)
    PUBLICATION_PATTERN = re.compile(r"\b(co-authored|first author|published in|conference paper|journal paper|ieee|acm|arxiv|proceedings of)\b", re.IGNORECASE)
    FACULTY_COLLAB_PATTERN = re.compile(r"\b(under the guidance of Professor|in collaboration with Dr\.|personal discussions with)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", re.IGNORECASE)
    AWARD_PATTERN = re.compile(r"\b(awarded first place|won the|gold medalist|national champion|best paper award)\b", re.IGNORECASE)

    @classmethod
    def validate_and_sanitize_draft(
        cls,
        draft_text: str,
        profile: StudentProfile,
        opportunity: Opportunity,
    ) -> Tuple[str, List[str], List[str]]:
        """
        Audits draft sentences against student facts.
        Returns:
            (sanitized_text, verified_claims, flagged_or_redacted_claims)
        """
        verified_claims: List[str] = [
            f"Undergraduate Degree: {profile.current_degree}",
            f"Major/Discipline: {profile.major}",
            f"Confirmed CGPA: {profile.cgpa}/{profile.gpa_scale}",
            f"Target Program: {opportunity.degree_level} at {opportunity.university_or_provider}",
            f"English Proficiency: {profile.english_test_status}",
        ]
        for skill in profile.skills[:5]:
            verified_claims.append(f"Confirmed Skill: {skill}")
        for proj in profile.projects:
            verified_claims.append(f"Confirmed Project: {proj}")

        flagged_claims: List[str] = []
        sanitized_lines: List[str] = []

        confirmed_text = (
            f"{profile.full_name} {profile.current_degree} {profile.major} "
            f"{' '.join(profile.skills)} {' '.join(profile.projects)} "
            f"{profile.english_test_status} {profile.nationality}"
        ).lower()

        for line in draft_text.split("\n"):
            current_line = line

            # 1. Audit fabricated accuracy or metric claims
            metric_matches = cls.METRIC_PATTERN.findall(current_line)
            for m in metric_matches:
                if m.lower() not in confirmed_text:
                    flagged_claims.append(f"Unverified performance metric '{m}' detected; replaced with student verification placeholder.")
                    current_line = cls.METRIC_PATTERN.sub("[Insert Verified Metric / Quantitative Result]", current_line)

            # 2. Audit publication claims
            pub_match = cls.PUBLICATION_PATTERN.search(current_line)
            if pub_match and not any(k in confirmed_text for k in ["publication", "published", "paper"]):
                flagged_claims.append(f"Unsupported publication claim ('{pub_match.group(0)}') detected; redacted.")
                current_line = re.sub(
                    r"([^.]*?" + re.escape(pub_match.group(0)) + r"[^.]*\.)",
                    "[Insert Verified Publication or Relevant Project Detail if applicable].",
                    current_line,
                    flags=re.IGNORECASE
                )

            # 3. Audit specific professor relationship claims
            fac_match = cls.FACULTY_COLLAB_PATTERN.search(current_line)
            if fac_match:
                prof_name = fac_match.group(2)
                if prof_name.lower() not in confirmed_text:
                    flagged_claims.append(f"Unconfirmed faculty relationship with '{prof_name}' flagged.")
                    current_line = cls.FACULTY_COLLAB_PATTERN.sub("under the prospective guidance of [Insert Professor / Faculty Advisor Name]", current_line)

            # 4. Audit fabricated award claims
            award_match = cls.AWARD_PATTERN.search(current_line)
            if award_match and not any(k in confirmed_text for k in ["award", "gold medal", "first place", "won"]):
                flagged_claims.append(f"Unconfirmed award/achievement claim '{award_match.group(0)}' flagged.")
                current_line = cls.AWARD_PATTERN.sub("[Insert Verified Academic Honors / Distinction]", current_line)

            sanitized_lines.append(current_line)

        sanitized_text = "\n".join(sanitized_lines)
        return sanitized_text, verified_claims, flagged_claims
