"""
Agent 5: Application Drafting Agent
File: agents/application_agent.py

Responsibilities:
1. Retrieve verified opportunity requirements and confirmed student profile facts.
2. Prepare a tailored, professional Statement of Purpose (SOP) draft.
3. Align strictly with real program details and student-supplied goals.
4. Guard against hallucination: never invent publications, awards, or fake achievements.
5. Provide a clear personalization checklist.
6. Support TXT and DOCX exports.
"""
from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import io
import docx

from models.schemas import StudentProfile, Opportunity, ApplicationDraft, AgentEvent
from services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class ApplicationDraftingAgent:
    """Agent that creates tailored statements of purpose from verified evidence only."""

    def __init__(self, gemini_client: GeminiClient | None = None):
        self.gemini = gemini_client or GeminiClient()

    def generate_draft(
        self,
        opportunity: Opportunity,
        profile: StudentProfile,
        events_collector: List[AgentEvent] | None = None
    ) -> ApplicationDraft:
        """
        Synthesizes an application draft strictly grounded on confirmed facts.
        """
        if events_collector is not None:
            events_collector.append(
                AgentEvent(
                    agent_name="Application Drafting Agent",
                    action="Drafting Statement of Purpose",
                    status="in_progress",
                    detail=f"Synthesizing customized draft for {opportunity.university_or_provider} ({opportunity.name})."
                )
            )

        verified_facts = [
            f"Candidate: {profile.full_name}",
            f"Undergraduate Degree: {profile.current_degree} in {profile.major}",
            f"Academic Standing: CGPA {profile.cgpa}/{profile.gpa_scale}",
            f"Technical Skills: {', '.join(profile.skills)}",
            f"Projects: {'; '.join(profile.projects)}",
            f"Target Program: {opportunity.degree_level} in {opportunity.subject_area}",
            f"Target Institution: {opportunity.university_or_provider}",
            f"Scholarship/Award: {opportunity.name}",
            f"Language Readiness: {profile.english_test_status}"
        ]

        unverified_avoided = [
            "Fabricated co-authored publications or conference papers",
            "Unconfirmed financial distress or artificial hardship claims",
            "Invented faculty relationships or imaginary prior campus visits",
            "Unverified test scores or inflated GPA metrics"
        ]

        checklist = [
            f"1. Review faculty directory at {opportunity.university_or_provider} and specify 1-2 prospective professors whose research aligns with your interests.",
            f"2. Detail how your undergraduate projects ({profile.projects[0] if profile.projects else 'your capstone'}) sparked your interest in {opportunity.subject_area}.",
            f"3. Tailor the specific elective course modules offered under {opportunity.name}.",
            f"4. Confirm official submission word limit (typically 500-1000 words) on {opportunity.official_url}."
        ]

        draft_content = ""

        # Attempt generation via live Gemini if available
        if self.gemini.is_live:
            prompt = (
                f"You are an expert academic advisor writing an authentic Statement of Purpose for graduate admission.\n"
                f"Student Profile:\n"
                f"- Name: {profile.full_name}\n"
                f"- Degree: {profile.current_degree} ({profile.major}), CGPA: {profile.cgpa}/{profile.gpa_scale}\n"
                f"- Verified Skills: {', '.join(profile.skills)}\n"
                f"- Projects: {'; '.join(profile.projects)}\n"
                f"Target University: {opportunity.university_or_provider}\n"
                f"Target Degree & Subject: {opportunity.degree_level} in {opportunity.subject_area}\n"
                f"Funding Opportunity: {opportunity.name} ({opportunity.funding_type})\n\n"
                f"CRITICAL RULES:\n"
                f"1. Only use facts listed above. Do not invent publications, fake companies, or false test scores.\n"
                f"2. Where personal reflection or specific professor names are needed, use clear placeholders like [Insert Specific Professor Name].\n"
                f"3. Maintain a rigorous, compelling, and academic tone suitable for competitive international graduate admissions."
            )
            res = self.gemini.generate_content(
                prompt=prompt,
                system_instruction="You write strictly grounded, authentic academic graduate application essays without hallucinating unverified facts."
            )
            if res.get("success") and res.get("text"):
                candidate = res["text"].strip()
                # A usable draft must identify the applicant and preserve the
                # core academic fact package.  If a model omits either, use the
                # deterministic template instead of silently presenting a
                # generic, unverifiable essay as personalised.
                required_markers = [profile.full_name.lower(), str(profile.cgpa).lower()]
                if all(marker in candidate.lower() for marker in required_markers):
                    draft_content = candidate
                else:
                    logger.warning("Model SOP omitted required verified facts; using grounded fallback.")

        # Deterministic evidence-grounded fallback draft (when offline or demo mode)
        if not draft_content:
            projects_text = "\n".join([f"  • {p}" for p in profile.projects])
            draft_content = f"""STATEMENT OF PURPOSE

Applicant: {profile.full_name}
Target Program: {opportunity.degree_level} in {opportunity.subject_area}
Institution: {opportunity.university_or_provider}
Funding / Fellowship: {opportunity.name} ({opportunity.funding_type})
Target Intake: {opportunity.target_intake}

Dear Members of the Graduate Admissions and Scholarship Committee,

I am writing to formally submit my application for admission to the {opportunity.degree_level} in {opportunity.subject_area} at {opportunity.university_or_provider}, alongside consideration for the {opportunity.name}. Having established a rigorous academic foundation through my {profile.current_degree} in {profile.major}, graduating with a cumulative grade point average of {profile.cgpa} on a {profile.gpa_scale} scale, I am eager to deepen my technical expertise and contribute actively to advanced graduate research.

ACADEMIC AND TECHNICAL FOUNDATION
Throughout my undergraduate training, I maintained a disciplined focus on computational fundamentals, algorithms, and practical software engineering. My core proficiencies encompass {', '.join(profile.skills[:6])}, which I have applied systematically across both coursework and substantial practical implementations. My technical perspective has been shaped by direct engineering engagements, including:
{projects_text}

These experiences exposed me to real-world challenges in data processing, model evaluation, and computational efficiency, underscoring the critical necessity of pursuing specialized postgraduate studies.

RESEARCH ALIGNMENT WITH {opportunity.university_or_provider.upper()}
The postgraduate program at {opportunity.university_or_provider} stands out internationally for its distinguished faculty, cutting-edge facilities, and vibrant research culture in {opportunity.subject_area}. I am particularly drawn to current departmental work focusing on [Insert Specific Research Group / Lab Focus]. In particular, I look forward to the prospect of contributing to research under the guidance of [Insert Professor / Faculty Advisor Name], whose ongoing contributions closely match my aspirations.

SCHOLARSHIP MOTIVATION AND VALUE CREATION
Receiving the {opportunity.name} would be instrumental in allowing me to dedicate myself entirely to high-impact graduate research and academic excellence. By alleviating financial constraints through its {opportunity.funding_type} provision, this award will enable me to participate fully in lab seminars, collaborative projects, and the academic community at {opportunity.university_or_provider}.

With verified readiness ({profile.english_test_status}), academic dedication, and proven engineering discipline, I am prepared to meet the demanding standards of your program and represent {opportunity.university_or_provider} with distinction.

Sincerely,
{profile.full_name}
"""

        # Phase 2: Claim Validation against confirmed student facts & evidence
        from services.claim_validator import ClaimValidator
        sanitized_content, validated_claims, flagged_claims = ClaimValidator.validate_and_sanitize_draft(
            draft_text=draft_content,
            profile=profile,
            opportunity=opportunity,
        )

        all_avoided = unverified_avoided + [f"Flagged/Redacted: {fc}" for fc in flagged_claims]

        draft = ApplicationDraft(
            opportunity_id=opportunity.id,
            opportunity_name=opportunity.name,
            university=opportunity.university_or_provider,
            document_type="Statement of Purpose",
            content=sanitized_content,
            personalization_checklist=checklist,
            verified_facts_used=verified_facts + validated_claims,
            unverified_claims_avoided=all_avoided,
            generated_timestamp=datetime.utcnow().isoformat()
        )

        if events_collector is not None:
            events_collector.append(
                AgentEvent(
                    agent_name="Application Drafting Agent",
                    action="Draft Complete",
                    status="completed",
                    detail=f"Generated editable Statement of Purpose with {len(checklist)} personalization action items."
                )
            )

        return draft

    @classmethod
    def export_as_docx(cls, draft: ApplicationDraft) -> bytes:
        """Generates a downloadable DOCX document in memory."""
        doc = docx.Document()
        doc.add_heading(draft.document_type, level=0)
        doc.add_heading(f"{draft.opportunity_name} — {draft.university}", level=2)

        for line in draft.content.split("\n"):
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.isupper() and len(line_str) < 50:
                doc.add_heading(line_str, level=3)
            else:
                doc.add_paragraph(line_str)

        doc.add_heading("Personalization Action Checklist", level=2)
        for item in draft.personalization_checklist:
            doc.add_paragraph(item, style='List Bullet')

        doc.add_heading("Verified Evidence Audit", level=2)
        for fact in draft.verified_facts_used:
            doc.add_paragraph(fact, style='List Bullet')

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
