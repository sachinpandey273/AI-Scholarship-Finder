"""
Transparent and deterministic Python scoring module.
Calculates the 100-point match score from explicit validated fields
as specified in the Hackathon master guidelines:
  - Eligibility evidence: 30 pts
  - Funding suitability: 25 pts
  - Academic & subject fit: 15 pts
  - Skills & project relevance: 10 pts
  - Preferred-country fit: 10 pts
  - Deadline & readiness: 10 pts
"""
from __future__ import annotations

from typing import Tuple, List, Dict
from models.schemas import StudentProfile, Opportunity, MatchScore

def calculate_match_score(profile: StudentProfile, opp: Opportunity) -> MatchScore:
    """
    Computes a transparent, reproducible 100-point match score.
    Returns MatchScore object with detailed breakdown, reason, and uncertainties.
    """
    breakdown: Dict[str, str] = {}
    uncertainties: List[str] = []

    # -------------------------------------------------------------
    # 1. Eligibility Evidence (30 Points Max)
    # -------------------------------------------------------------
    elig_status = opp.eligibility.status if opp.eligibility else "insufficient_information"
    elig_score = 0.0

    if elig_status == "likely_eligible":
        # Check source confidence
        has_direct_official = any(s.confidence_policy == "official_direct" for s in opp.source_evidence)
        elig_score = 30.0 if has_direct_official else 26.0
        breakdown["eligibility_evidence"] = f"{elig_score}/30 (Status: likely_eligible, Official verified)"
    elif elig_status == "potential_fit":
        elig_score = 16.0
        breakdown["eligibility_evidence"] = "16.0/30 (Status: potential_fit - pending specific criteria verification)"
        if opp.eligibility and opp.eligibility.missing_or_unresolved_criteria:
            uncertainties.extend(opp.eligibility.missing_or_unresolved_criteria)
    elif elig_status == "insufficient_information":
        elig_score = 6.0
        breakdown["eligibility_evidence"] = "6.0/30 (Status: insufficient_information - unconfirmed source facts)"
        uncertainties.append("Official verification evidence incomplete")
    else:  # not_eligible
        elig_score = 0.0
        breakdown["eligibility_evidence"] = "0.0/30 (Hard Exclusion: not_eligible due to criteria conflict)"

    # -------------------------------------------------------------
    # 2. Funding Suitability (25 Points Max)
    # -------------------------------------------------------------
    fund_score = 0.0
    ftype = opp.funding_type.lower()

    if "living stipend" in ftype or "full tuition + living" in ftype:
        fund_score = 25.0
        breakdown["funding_suitability"] = "25.0/25 (Comprehensive Full Tuition + Living Stipend Coverage)"
    elif "full tuition" in ftype:
        fund_score = 20.0
        breakdown["funding_suitability"] = "20.0/25 (100% Full Tuition Waiver, student covers living expenses)"
    elif "substantial" in ftype:
        fund_score = 15.0
        breakdown["funding_suitability"] = "15.0/25 (Substantial Partial Scholarship covering 40%-75% tuition)"
    elif "merit" in ftype:
        fund_score = 12.0
        breakdown["funding_suitability"] = "12.0/25 (Competitive Merit Award / partial stipend grant)"
    elif "need" in ftype or "fee waiver" in ftype:
        fund_score = 10.0
        breakdown["funding_suitability"] = "10.0/25 (Need-based assistance or administrative fee waiver)"
    else:
        fund_score = 5.0
        breakdown["funding_suitability"] = "5.0/25 (Partial or departmental support)"

    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # 3. Academic and Subject Fit (15 Points Max)
    # -------------------------------------------------------------
    acad_score = 0.0
    # Strict Degree level alignment (7.5 pts)
    target_deg_low = profile.target_degree.lower()
    opp_deg_low = opp.degree_level.lower()

    is_student_phd = any(k in target_deg_low for k in ["phd", "doctor", "dphil"])
    is_opp_phd = any(k in opp_deg_low for k in ["phd", "doctor", "dphil"])

    is_student_masters = any(k in target_deg_low for k in ["master", "msc", "ms", "meng", "mmath", "mcomp", "postgraduate"])
    is_opp_masters = any(k in opp_deg_low for k in ["master", "msc", "ms", "meng", "mmath", "mcomp", "postgraduate"])

    # Strict check: Degree level mismatch cannot receive degree points
    has_degree_mismatch = False
    if is_student_phd and not is_opp_phd:
        deg_pts = 0.0
        has_degree_mismatch = True
        uncertainties.append(f"Hard degree mismatch: Candidate targets PhD, but program offers {opp.degree_level} only.")
    elif is_student_masters and not is_student_phd and is_opp_phd and not is_opp_masters and "direct phd" not in opp_deg_low:
        deg_pts = 0.0
        has_degree_mismatch = True
        uncertainties.append(f"Hard degree mismatch: Candidate targets Master's, but program is a doctoral route ({opp.degree_level}).")
    elif (is_student_phd and is_opp_phd) or (is_student_masters and is_opp_masters):
        deg_pts = 7.5
    elif "postgraduate" in opp_deg_low:
        deg_pts = 5.0
    else:
        deg_pts = 0.0

    # Subject alignment (7.5 pts)
    target_subj_low = (profile.target_subject + " " + profile.major).lower()
    opp_subj_low = opp.subject_area.lower()
    keywords = ["computer", "ai", "machine learning", "data", "software", "tech", "informatics", "computational"]
    matched_subj = any(kw in opp_subj_low for kw in keywords if kw in target_subj_low)
    subj_pts = 7.5 if matched_subj else 4.0

    acad_score = deg_pts + subj_pts
    breakdown["academic_subject_fit"] = f"{acad_score}/15 (Degree match: {deg_pts}pts, Subject match: {subj_pts}pts)"

    # -------------------------------------------------------------
    # 4. Skills and Project Relevance (10 Points Max)
    # -------------------------------------------------------------
    student_tokens = set([s.lower() for s in profile.skills])
    for proj in profile.projects:
        for word in proj.lower().split():
            if len(word) > 3:
                student_tokens.add(word)

    opp_text = f"{opp.name} {opp.subject_area} {opp.academic_eligibility_reqs}".lower()
    matches = [token for token in student_tokens if token in opp_text]

    if len(matches) >= 3:
        skills_score = 10.0
    elif len(matches) >= 1:
        skills_score = 7.0
    else:
        skills_score = 4.0  # general baseline relevance in computing
    breakdown["skills_project_relevance"] = f"{skills_score}/10 (Matched profile skill tokens: {len(matches)})"

    # -------------------------------------------------------------
    # 5. Preferred Country Fit (10 Points Max)
    # -------------------------------------------------------------
    norm_preferred = [c.strip().lower() for c in profile.preferred_countries]
    opp_country_norm = opp.country.strip().lower()

    if any(pref in opp_country_norm or opp_country_norm in pref for pref in norm_preferred):
        country_score = 10.0
        breakdown["preferred_country_fit"] = f"10.0/10 (Direct destination match: {opp.country})"
    else:
        country_score = 2.0
        breakdown["preferred_country_fit"] = f"2.0/10 (Outside primary preferred list: {opp.country})"
        uncertainties.append(f"Destination {opp.country} is not listed in student preferred countries")

    # -------------------------------------------------------------
    # 6. Deadline and Application Readiness (10 Points Max)
    # -------------------------------------------------------------
    dstatus = opp.deadline_status.lower()
    if dstatus in ["open", "active"]:
        deadline_score = 10.0
        breakdown["deadline_readiness"] = f"10.0/10 (Active open application cycle: {opp.deadline})"
    elif dstatus in ["rolling", "rolling_admissions"]:
        deadline_score = 9.0
        breakdown["deadline_readiness"] = f"9.0/10 (Rolling admissions policy: {opp.deadline})"
    elif dstatus in ["future", "upcoming_not_open"]:
        deadline_score = 5.0
        breakdown["deadline_readiness"] = f"5.0/10 (Upcoming intake cycle announced but not open: {opp.deadline})"
        uncertainties.append("Application cycle is upcoming; submissions not yet open")
    elif dstatus == "unknown":
        deadline_score = 2.0
        breakdown["deadline_readiness"] = "2.0/10 (Specific round deadline unconfirmed)"
        uncertainties.append("Application deadline unconfirmed on primary page")
    else:  # closed or extended_pending_verification
        deadline_score = 0.0
        breakdown["deadline_readiness"] = f"0.0/10 (Application closed for current round: {opp.deadline})"
        uncertainties.append("Application cycle currently closed")

    # Prevent funding score from compensating for fundamental degree or eligibility mismatch
    if has_degree_mismatch or elig_status == "not_eligible":
        fund_score = 0.0
        breakdown["funding_suitability"] += " [NULLIFIED: Disqualified due to hard eligibility/degree mismatch]"

    total_score = round(
        elig_score + fund_score + acad_score + skills_score + country_score + deadline_score, 1
    )

    reason = (
        f"Ranked {total_score}/100 based on {opp.funding_type} funding, {opp.country} location match, "
        f"and {elig_status} verification status."
    )

    return MatchScore(
        total_score=total_score,
        eligibility_evidence_score=elig_score,
        funding_suitability_score=fund_score,
        academic_subject_fit_score=acad_score,
        skills_project_relevance_score=skills_score,
        preferred_country_fit_score=country_score,
        deadline_readiness_score=deadline_score,
        score_breakdown=breakdown,
        reason=reason,
        uncertainties=uncertainties,
    )
