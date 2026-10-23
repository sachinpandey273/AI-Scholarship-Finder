"""
Agent 4: Scholarship Matching and Ranking Agent
File: agents/matching_agent.py

Responsibilities:
1. Match verified opportunities to the normalized student profile.
2. Exclude confirmed-ineligible opportunities from top recommendations.
3. Calculate transparent 100-point scores in Python using utils.scoring.
4. Explain every recommendation and uncertainty.
5. Rank suitable opportunities.
6. Return the top 5 defensible matches (or fewer with explanation).
7. Preserve all researched candidates for full research export and inspection.
"""
from __future__ import annotations

import logging
from typing import List, Tuple, Dict, Any

from models.schemas import StudentProfile, Opportunity, MatchScore, AgentEvent
from utils.scoring import calculate_match_score

logger = logging.getLogger(__name__)

class MatchingAgent:
    """Agent executing scoring, hard filtering, and ranking of verified opportunities."""

    def rank_opportunities(
        self,
        opportunities: List[Opportunity],
        profile: StudentProfile,
        events_collector: List[AgentEvent] | None = None
    ) -> Tuple[List[Opportunity], List[Opportunity], str]:
        """
        Scores all opportunities, filters ineligible candidates, and returns:
          (top_five_recommendations, all_scored_opportunities, ranking_summary)
        """
        if events_collector is not None:
            events_collector.append(
                AgentEvent(
                    agent_name="Matching & Ranking Agent",
                    action="Calculating Scores",
                    status="in_progress",
                    detail="Executing 100-point multi-factor Python ranking formula across all candidates."
                )
            )

        scored_list: List[Opportunity] = []
        eligible_candidates: List[Opportunity] = []

        target_deg_low = profile.target_degree.lower()
        is_student_phd = any(k in target_deg_low for k in ["phd", "doctor", "dphil"])
        is_student_masters = any(k in target_deg_low for k in ["master", "msc", "ms", "meng", "mmath", "mcomp", "postgraduate"])

        for opp in opportunities:
            opp.match_score = calculate_match_score(profile, opp)
            scored_list.append(opp)

            # Hard eligibility filter 1: exclude confirmed 'not_eligible' from top recommendations
            if opp.eligibility and opp.eligibility.status == "not_eligible":
                continue

            # Hard eligibility filter 2: exclude degree level mismatches
            opp_deg_low = opp.degree_level.lower()
            is_opp_phd = any(k in opp_deg_low for k in ["phd", "doctor", "dphil"])
            is_opp_masters = any(k in opp_deg_low for k in ["master", "msc", "ms", "meng", "mmath", "mcomp", "postgraduate"])

            if is_student_phd and not is_opp_phd:
                continue
            if is_student_masters and not is_student_phd and is_opp_phd and not is_opp_masters and "direct phd" not in opp_deg_low:
                continue

            # Hard eligibility filter 3: exclude closed opportunities from primary actionable recommendations
            if opp.deadline_status == "closed":
                continue

            # Also ensure total score is viable
            if opp.match_score.total_score >= 40.0:
                eligible_candidates.append(opp)

        # Sort descending by total_score
        eligible_candidates.sort(
            key=lambda x: (x.match_score.total_score if x.match_score else 0.0),
            reverse=True
        )

        scored_list.sort(
            key=lambda x: (x.match_score.total_score if x.match_score else 0.0),
            reverse=True
        )

        top_five = eligible_candidates[:5]
        shortfall_explanation = ""

        if len(top_five) < 5:
            shortfall_explanation = (
                f"Note: Found {len(top_five)} defensible recommendations meeting all hard eligibility "
                f"filters (out of {len(opportunities)} researched candidates). Remaining candidates either "
                f"exhibited hard eligibility exclusions or insufficient criteria alignment."
            )

        if events_collector is not None:
            events_collector.append(
                AgentEvent(
                    agent_name="Matching & Ranking Agent",
                    action="Ranking Complete",
                    status="completed",
                    detail=f"Selected top {len(top_five)} recommended opportunities. Scores range from {top_five[0].match_score.total_score if top_five else 0} down to {top_five[-1].match_score.total_score if top_five else 0}."
                )
            )

        return top_five, scored_list, shortfall_explanation
