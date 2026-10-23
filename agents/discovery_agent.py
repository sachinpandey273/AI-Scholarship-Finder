"""
Agent 2: Scholarship and Program Discovery Agent
File: agents/discovery_agent.py

Responsibilities:
1. Research opportunities matching student's degree, discipline, destinations, and funding.
2. Discover >10 candidates initially to allow for downstream filtering.
3. Remove duplicate programs and duplicate scholarships.
4. Identify official university or scholarship-provider websites.
5. Store official source URLs, citations, timestamps, and status.
6. Pass candidates to Verification Agent without declaring eligibility early.
"""
from __future__ import annotations

import logging
from typing import List, Set, Dict, Any
from datetime import datetime

from models.schemas import StudentProfile, Opportunity, AgentEvent
from services.web_research import WebResearchService
from services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class DiscoveryAgent:
    """Agent discovering authentic university and scholarship candidate opportunities."""

    def __init__(self, gemini_client: GeminiClient | None = None):
        self.gemini = gemini_client or GeminiClient()
        self.web_research = WebResearchService(self.gemini)

    def discover(
        self,
        profile: StudentProfile,
        events_collector: List[AgentEvent] | None = None
    ) -> List[Opportunity]:
        """
        Executes discovery research, deduplicates entries, and returns candidate opportunities.
        """
        if events_collector is not None:
            events_collector.append(
                AgentEvent(
                    agent_name="Discovery Agent",
                    action="Initiating Research",
                    status="in_progress",
                    detail=f"Searching verified university databases for {profile.target_subject} in {', '.join(profile.preferred_countries)}"
                )
            )

        # Retrieve candidates from web research service
        candidates = self.web_research.discover_opportunities(profile)

        # Deduplicate candidates by name and university
        deduped: List[Opportunity] = []
        seen_keys: Set[str] = set()

        for opp in candidates:
            key = f"{opp.university_or_provider.lower()}::{opp.name.lower()}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduped.append(opp)

        if events_collector is not None:
            events_collector.append(
                AgentEvent(
                    agent_name="Discovery Agent",
                    action="Discovery Complete",
                    status="completed",
                    detail=f"Discovered and deduplicated {len(deduped)} distinct candidate opportunities with official URLs."
                )
            )

        return deduped
