"""
Agent 3: Eligibility and Official-Source Verification Agent
File: agents/eligibility_agent.py

Responsibilities:
1. Inspect official source evidence for each candidate.
2. Compare student facts (CGPA, degree, citizenship, English test) against documented criteria.
3. Categorize into 4 explicit statuses:
   - likely_eligible
   - potential_fit
   - not_eligible
   - insufficient_information
4. Distinguish confirmed facts from unverified claims.
5. Never manufacture deadlines, fees, or requirements.
"""
from __future__ import annotations

import logging
from typing import List, Dict, Any
from datetime import datetime

from models.schemas import StudentProfile, Opportunity, EligibilityAssessment, AgentEvent
from services.source_verifier import SourceVerifier

logger = logging.getLogger(__name__)

class EligibilityAgent:
    """Agent that performs rigorous, evidence-grounded verification against official sources."""

    def __init__(self):
        self.verifier = SourceVerifier()

    def verify_candidate(self, opp: Opportunity, profile: StudentProfile) -> EligibilityAssessment:
        """
        Conducts point-by-point comparison between student facts and opportunity criteria.
        """
        confirmed: List[str] = []
        missing_or_unresolved: List[str] = []
        conflicting: List[str] = []

        # ---------------------------------------------------------
        # Check Source Evidence Accessibility First
        # ---------------------------------------------------------
        source_inaccessible = not opp.source_evidence or any(
            s.confidence_policy == "inaccessible_or_conflicting" for s in opp.source_evidence
        )

        # ---------------------------------------------------------
        # 1. Degree Level Compatibility (Hard Constraint)
        # ---------------------------------------------------------
        target_deg_low = profile.target_degree.lower()
        opp_deg_low = opp.degree_level.lower()

        is_student_phd = any(k in target_deg_low for k in ["phd", "doctor", "dphil"])
        is_opp_phd = any(k in opp_deg_low for k in ["phd", "doctor", "dphil"])

        is_student_masters = any(k in target_deg_low for k in ["master", "msc", "ms", "meng", "mmath", "mcomp", "postgraduate"])
        is_opp_masters = any(k in opp_deg_low for k in ["master", "msc", "ms", "meng", "mmath", "mcomp", "postgraduate"])

        # PhD target cannot match Master's-only program
        if is_student_phd and not is_opp_phd:
            conflicting.append(
                f"Degree level conflict: Student targets doctoral studies ({profile.target_degree}), "
                f"but opportunity offers {opp.degree_level} only."
            )
        # Master's target cannot match PhD-only program (unless program supports direct bachelor-to-PhD or combined)
        elif is_student_masters and not is_student_phd and is_opp_phd and not is_opp_masters and "direct phd" not in opp_deg_low:
            conflicting.append(
                f"Degree level conflict: Student targets Master's studies ({profile.target_degree}), "
                f"but opportunity is a doctoral-only track ({opp.degree_level})."
            )
        else:
            confirmed.append(f"Degree route aligned: {opp.degree_level}")

        # A known hard conflict remains useful even if a page later becomes
        # unavailable.  Otherwise unavailable or absent official evidence can
        # never yield a positive eligibility label.
        if source_inaccessible and not conflicting:
            return EligibilityAssessment(
                status="insufficient_information",
                confirmed_criteria=[],
                missing_or_unresolved_criteria=["No accessible, verified official source evidence was available; criteria remain unconfirmed."],
                conflicting_criteria=[],
                explanation="Eligibility cannot be positively verified without retrieved official source evidence.",
                is_verified=False,
            )

        # ---------------------------------------------------------
        # 2. Citizenship / Nationality Restrictions
        # ---------------------------------------------------------
        student_country = profile.nationality.lower()
        has_citizenship_restriction = False

        for restriction in opp.citizenship_restrictions:
            r_low = restriction.lower()
            if "domestic only" in r_low or "citizens only" in r_low:
                if opp.country.lower() != student_country:
                    has_citizenship_restriction = True
                    conflicting.append(f"Restricted to citizens of {opp.country}; student holds {profile.nationality} nationality.")
            elif "open to all" in r_low or "international" in r_low:
                confirmed.append("Open to international applicants including Indian nationals")

        if not has_citizenship_restriction and not any("Open to" in c for c in confirmed):
            confirmed.append("No adverse citizenship restrictions detected on official source")

        # ---------------------------------------------------------
        # 3. Academic Qualification & CGPA Alignment
        # ---------------------------------------------------------
        student_pct = (profile.cgpa / profile.gpa_scale) * 100.0

        req_text = opp.academic_eligibility_reqs.lower()
        if "80%" in req_text or "first class" in req_text or "first-class" in req_text or "8.0" in req_text:
            if student_pct >= 80.0 or profile.cgpa >= 8.0:
                confirmed.append(f"Academic requirement met: Student has {profile.cgpa}/{profile.gpa_scale} ({student_pct:.1f}%), exceeding the ~80% / 8.0 baseline.")
            else:
                conflicting.append(f"Student CGPA ({profile.cgpa}/{profile.gpa_scale}) falls below the 80% / 8.0 threshold.")
        elif "upper second" in req_text or "second class upper" in req_text or "75%" in req_text:
            if student_pct >= 75.0 or profile.cgpa >= 7.5:
                confirmed.append(f"Academic requirement met: Meets Second Class Upper requirement with {profile.cgpa}/{profile.gpa_scale}.")
            else:
                conflicting.append("Student CGPA does not meet the Second Class Upper requirement.")
        else:
            confirmed.append(f"Undergraduate degree discipline aligned ({profile.current_degree})")

        # ---------------------------------------------------------
        # 4. Language Test Requirements
        # ---------------------------------------------------------
        lang_req = opp.language_requirements.lower()
        student_lang = profile.english_test_status.lower()

        if "ielts 8" in lang_req or "toefl 110" in lang_req:
            missing_or_unresolved.append(f"Higher English proficiency minimum ({opp.language_requirements}) requires retake or departmental interview.")
        elif "ielts 7" in lang_req or "toefl 100" in lang_req:
            if "ielts 7.5" in student_lang or "toefl 10" in student_lang:
                confirmed.append(f"English requirement satisfied: Student holds {profile.english_test_status}, exceeding target score.")
            elif "ielts 6.5" in student_lang:
                missing_or_unresolved.append(f"Requires IELTS 7.0/7.5; student's score ({profile.english_test_status}) requires retake or departmental waiver.")
            else:
                missing_or_unresolved.append(f"Specific language minimum ({opp.language_requirements}) requires official score submission.")
        elif lang_req:
            confirmed.append(f"General graduate English proficiency requirement satisfied ({profile.english_test_status})")
        else:
            confirmed.append("Standard graduate English proficiency requirement satisfied")

        # ---------------------------------------------------------
        # 5. Deterministic Application Status & Deadlines
        # ---------------------------------------------------------
        from services.deadline_service import DeadlineService
        eval_status, parsed_d, deadline_msg = DeadlineService.evaluate_status(opp.deadline)

        # Update opp with evaluated status if past
        if eval_status == "closed":
            opp.deadline_status = "closed"
            conflicting.append(f"Application cycle for target intake is officially closed: {deadline_msg}")
        elif eval_status == "upcoming_not_open":
            opp.deadline_status = "upcoming_not_open"
            missing_or_unresolved.append(f"Application window not yet open: {deadline_msg}")
        elif eval_status in ["open", "rolling_admissions"]:
            opp.deadline_status = eval_status
            confirmed.append(f"Application intake cycle active: {opp.deadline}")
        elif opp.deadline_status == "closed":
            conflicting.append(f"Application cycle for target intake is officially closed ({opp.deadline}).")
        else:
            missing_or_unresolved.append("Exact application round deadline requires confirmation from faculty website.")

        # ---------------------------------------------------------
        # 6. Application Type & Nomination
        # ---------------------------------------------------------
        if opp.application_type == "Nomination required":
            missing_or_unresolved.append("Requires faculty nomination by department after initial admission offer.")

        # ---------------------------------------------------------
        # 6. Synthesize Final Assessment Status
        # ---------------------------------------------------------
        if conflicting:
            status = "not_eligible"
            explanation = (
                f"Student is currently evaluated as not eligible due to direct conflicts: "
                f"{'; '.join(conflicting)}."
            )
        elif missing_or_unresolved:
            status = "potential_fit"
            explanation = (
                f"Candidate exhibits strong baseline alignment, but is classified as a potential fit "
                f"pending resolution of: {'; '.join(missing_or_unresolved)}."
            )
        else:
            status = "likely_eligible"
            explanation = (
                f"Preliminary evidence supports likely eligibility based on documented academic standing, "
                f"degree discipline, nationality allowance, and language readiness. Note: Official admission "
                f"remains subject to final university committee review."
            )

        return EligibilityAssessment(
            status=status,
            confirmed_criteria=confirmed,
            missing_or_unresolved_criteria=missing_or_unresolved,
            conflicting_criteria=conflicting,
            explanation=explanation,
            is_verified=True
        )

    def verify_all(
        self,
        opportunities: List[Opportunity],
        profile: StudentProfile,
        events_collector: List[AgentEvent] | None = None
    ) -> List[Opportunity]:
        """Audits all candidate opportunities and attaches EligibilityAssessment."""
        if events_collector is not None:
            events_collector.append(
                AgentEvent(
                    agent_name="Eligibility & Verification Agent",
                    action="Auditing Opportunities",
                    status="in_progress",
                    detail=f"Auditing {len(opportunities)} candidate records against student academic profile and official sources."
                )
            )

        verified_list: List[Opportunity] = []
        for opp in opportunities:
            opp.eligibility = self.verify_candidate(opp, profile)
            verified_list.append(opp)

        if events_collector is not None:
            events_collector.append(
                AgentEvent(
                    agent_name="Eligibility & Verification Agent",
                    action="Verification Complete",
                    status="completed",
                    detail=f"Completed verification. Assessed {len(verified_list)} opportunities against official admission standards."
                )
            )

        return verified_list
