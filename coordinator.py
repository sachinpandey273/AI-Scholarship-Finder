"""
Central Workflow Coordinator
File: coordinator.py

Orchestrates the cooperating multi-agent workflow:
1. Profile Analyst Agent (document extraction + GitHub enrichment)
2. Discovery Agent (web search + candidate discovery + deduplication)
3. Eligibility & Verification Agent (official source checks + criteria audit)
4. Matching & Ranking Agent (deterministic 100-pt Python formula + top 5)
5. Application Drafting Agent (grounded Statement of Purpose draft + checklist)

Implements workflow run IDs, event logging, fault tolerance, and result persistence.
"""
from __future__ import annotations

import uuid
import time
import json
import logging
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from datetime import datetime

from config import AppConfig
from models.schemas import (
    StudentProfile,
    Opportunity,
    AgentEvent,
    WorkflowResult,
    ApplicationDraft,
)
from agents.profile_agent import ProfileAnalystAgent
from agents.discovery_agent import DiscoveryAgent
from agents.eligibility_agent import EligibilityAgent
from agents.matching_agent import MatchingAgent
from agents.application_agent import ApplicationDraftingAgent
from services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class WorkflowCoordinator:
    """Central orchestrator managing multi-agent pipeline execution and state transitions."""

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini = gemini_client or GeminiClient()
        self.profile_agent = ProfileAnalystAgent()
        self.discovery_agent = DiscoveryAgent(self.gemini)
        self.eligibility_agent = EligibilityAgent()
        self.matching_agent = MatchingAgent()
        self.drafting_agent = ApplicationDraftingAgent(self.gemini)

    def run_pipeline(
        self,
        resume_path: Optional[str | Path] = None,
        transcript_path: Optional[str | Path] = None,
        manual_overrides: Optional[Dict[str, Any]] = None,
        github_url_or_user: Optional[str] = None,
        target_opportunity_id: Optional[str] = None,
        progress_callback: Optional[Callable[[AgentEvent], None]] = None,
    ) -> WorkflowResult:
        """
        Executes the end-to-end multi-agent scholarship discovery and drafting pipeline.
        Recovers gracefully from partial step failures and records real agent events.
        """
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        events: List[AgentEvent] = []
        warnings: List[str] = []

        def log_event(agent: str, action: str, status: str, detail: str) -> AgentEvent:
            ev = AgentEvent(agent_name=agent, action=action, status=status, detail=detail)  # type: ignore
            events.append(ev)
            if progress_callback:
                try:
                    progress_callback(ev)
                except Exception as cb_err:
                    logger.warning(f"Progress callback warning: {cb_err}")
            return ev

        log_event(
            agent="Workflow Coordinator",
            action="Workflow Initialized",
            status="started",
            detail=f"Starting coordinated run ID: {run_id} (Demo mode: {not self.gemini.is_live})"
        )

        # -------------------------------------------------------------
        # Step 1: Student Profile Analyst Agent
        # -------------------------------------------------------------
        log_event(
            agent="Profile Analyst Agent",
            action="Profile Extraction",
            status="in_progress",
            detail="Extracting student qualifications from provided documents and inputs."
        )
        try:
            profile = self.profile_agent.analyze_profile(
                resume_path=resume_path,
                transcript_path=transcript_path,
                manual_overrides=manual_overrides,
                github_url_or_user=github_url_or_user,
            )
            log_event(
                agent="Profile Analyst Agent",
                action="Profile Validated",
                status="completed",
                detail=f"Profile compiled for {profile.full_name} ({profile.current_degree}, CGPA {profile.cgpa}/{profile.gpa_scale})."
            )
        except Exception as e:
            warnings.append(f"Profile agent error: {str(e)}. Proceeding with fallback profile.")
            profile = StudentProfile(
                full_name=manual_overrides.get("full_name", "Candidate") if manual_overrides else "Candidate",
                user_verified=True
            )
            log_event(
                agent="Profile Analyst Agent",
                action="Profile Fallback",
                status="warning",
                detail=f"Profile error handled: {str(e)[:80]}. Default baseline loaded."
            )

        # -------------------------------------------------------------
        # Step 2: Discovery Agent
        # -------------------------------------------------------------
        log_event(
            agent="Discovery Agent",
            action="Opportunity Discovery",
            status="in_progress",
            detail=f"Searching verified university databases for {profile.target_subject} across {profile.preferred_countries}."
        )
        discovered_candidates: List[Opportunity] = []
        try:
            discovered_candidates = self.discovery_agent.discover(profile, events_collector=events)
            log_event(
                agent="Discovery Agent",
                action="Discovery Complete",
                status="completed",
                detail=f"Successfully discovered {len(discovered_candidates)} distinct postgraduate opportunities."
            )
        except Exception as e:
            warnings.append(f"Discovery error: {str(e)}")
            log_event(
                agent="Discovery Agent",
                action="Discovery Failed",
                status="failed",
                detail=f"Failed during discovery: {str(e)[:80]}"
            )

        # -------------------------------------------------------------
        # Step 3: Eligibility & Verification Agent
        # -------------------------------------------------------------
        verified_opportunities: List[Opportunity] = []
        if discovered_candidates:
            try:
                verified_opportunities = self.eligibility_agent.verify_all(
                    opportunities=discovered_candidates,
                    profile=profile,
                    events_collector=events
                )
            except Exception as e:
                warnings.append(f"Verification error: {str(e)}")
                verified_opportunities = discovered_candidates

        # -------------------------------------------------------------
        # Step 4: Matching & Ranking Agent
        # -------------------------------------------------------------
        top_recommendations: List[Opportunity] = []
        ranked_candidates: List[Opportunity] = []
        shortfall_note = ""
        if verified_opportunities:
            try:
                top_recommendations, ranked_candidates, shortfall_note = self.matching_agent.rank_opportunities(
                    opportunities=verified_opportunities,
                    profile=profile,
                    events_collector=events
                )
                if shortfall_note:
                    warnings.append(shortfall_note)
            except Exception as e:
                warnings.append(f"Matching error: {str(e)}")
                top_recommendations = verified_opportunities[:5]
                ranked_candidates = verified_opportunities

        # -------------------------------------------------------------
        # Step 5: Application Drafting Agent
        # -------------------------------------------------------------
        draft: Optional[ApplicationDraft] = None
        # Select target opportunity (either user-selected ID or top recommendation)
        target_opp: Optional[Opportunity] = None
        if target_opportunity_id:
            for o in ranked_candidates:
                if o.id == target_opportunity_id:
                    target_opp = o
                    break
        if not target_opp and top_recommendations:
            target_opp = top_recommendations[0]

        if target_opp:
            try:
                draft = self.drafting_agent.generate_draft(
                    opportunity=target_opp,
                    profile=profile,
                    events_collector=events
                )
            except Exception as e:
                warnings.append(f"Application drafting error: {str(e)}")
                log_event(
                    agent="Application Drafting Agent",
                    action="Drafting Warning",
                    status="warning",
                    detail=f"Could not generate draft: {str(e)[:80]}"
                )

        elapsed = round(time.time() - start_time, 2)
        log_event(
            agent="Workflow Coordinator",
            action="Workflow Concluded",
            status="completed",
            detail=f"Run {run_id} completed in {elapsed}s with {len(top_recommendations)} recommendations."
        )

        # -------------------------------------------------------------
        # Step 6: Assemble & Persist Result
        # -------------------------------------------------------------
        result = WorkflowResult(
            run_id=run_id,
            student_profile=profile,
            discovered_candidates=ranked_candidates,
            verified_opportunities=ranked_candidates,
            top_recommendations=top_recommendations,
            execution_log=events,
            application_draft=draft,
            execution_time_seconds=elapsed,
            is_demo_mode=not self.gemini.is_live,
            warnings=warnings
        )

        # Persist result to local storage
        try:
            out_file = AppConfig.CACHE_DIR / f"{run_id}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, indent=2)
        except Exception as persist_err:
            logger.warning(f"Failed to persist run results: {persist_err}")

        return result
