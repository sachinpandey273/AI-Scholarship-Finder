"""
Core Pydantic data schemas for AI Scholarship Finder.
Validates all inputs, intermediary agent exchanges, and pipeline outputs.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

# =====================================================================
# Student Evidence & Profile Schemas
# =====================================================================

class StudentEvidence(BaseModel):
    """Tracks origin and certainty for every extracted student fact."""
    field_name: str = Field(description="Name of the attribute, e.g. 'cgpa', 'degree'")
    value: Any = Field(description="Extracted fact value")
    source_type: Literal["resume_pdf", "transcript_docx", "github", "manual_input", "unknown"]
    source_reference: str = Field(description="Filename, URL or user-entered identifier")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    extraction_note: Optional[str] = None

class StudentProfile(BaseModel):
    """Normalized student profile with evidence provenance."""
    full_name: str = Field(default="Candidate", description="Student's full display name")
    email: Optional[str] = None
    nationality: str = Field(default="India", description="Citizenship/nationality for eligibility filtering")
    current_degree: str = Field(default="BTech in Computer Science", description="Current/prior degree")
    major: str = Field(default="Computer Science", description="Primary major/discipline")
    cgpa: float = Field(default=8.2, ge=0.0, description="GPA or CGPA score")
    gpa_scale: float = Field(default=10.0, gt=0.0, description="Grading scale denominator, e.g. 10.0 or 4.0")
    expected_graduation_year: Optional[int] = Field(default=2025)
    skills: List[str] = Field(default_factory=list, description="Validated technical & research skills")
    projects: List[str] = Field(default_factory=list, description="Verified project titles or descriptions")
    github_username: Optional[str] = None
    github_repos_summary: Optional[str] = None
    target_degree: str = Field(default="Master of Science (MSc / MS)", description="Intended postgraduate degree")
    target_subject: str = Field(default="Computer Science / Artificial Intelligence")
    preferred_countries: List[str] = Field(default_factory=lambda: ["Canada", "Germany", "Singapore"])
    target_intake: str = Field(default="Fall 2026")
    english_test_status: str = Field(default="IELTS 7.5 / Met", description="English proficiency status or test result")
    funding_requirement: str = Field(default="Full funding or substantial tuition scholarship")
    evidence_chain: List[StudentEvidence] = Field(default_factory=list)
    unknown_fields: List[str] = Field(default_factory=list, description="Explicitly preserved unknown fields")
    user_verified: bool = Field(default=True, description="Whether the user reviewed the profile")

# =====================================================================
# Source & Verification Schemas
# =====================================================================

class FieldLevelEvidence(BaseModel):
    """Specific verifiable quote supporting an extracted field."""
    field_name: str
    extracted_value: str
    source_url: str
    exact_quote: str
    retrieval_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    verification_state: Literal[
        "discovered",
        "source_retrieved",
        "partially_verified",
        "verified",
        "conflicting_evidence",
        "unavailable"
    ] = "verified"

class SourceEvidence(BaseModel):
    """Documents retrieved web sources with confidence policy and field-level citations."""
    url: str
    title: str = ""
    domain: str = ""
    is_official: bool = True
    retrieval_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    excerpt: str = Field(description="Direct quotation or structured summary from source")
    confidence_policy: Literal[
        "official_direct",
        "official_unconfirmed",
        "third_party",
        "inaccessible_or_conflicting"
    ] = "official_direct"
    verification_state: Literal[
        "discovered",
        "source_retrieved",
        "partially_verified",
        "verified",
        "conflicting_evidence",
        "unavailable"
    ] = "verified"
    field_evidence: List[FieldLevelEvidence] = Field(default_factory=list)

class EligibilityAssessment(BaseModel):
    """Strict eligibility audit for an opportunity against student profile."""
    status: Literal["likely_eligible", "potential_fit", "not_eligible", "insufficient_information"]
    confirmed_criteria: List[str] = Field(default_factory=list)
    missing_or_unresolved_criteria: List[str] = Field(default_factory=list)
    conflicting_criteria: List[str] = Field(default_factory=list)
    explanation: str = ""
    is_verified: bool = True

class MatchScore(BaseModel):
    """Transparent 100-point formula scoring breakdown."""
    total_score: float = Field(ge=0.0, le=100.0)
    eligibility_evidence_score: float = Field(ge=0.0, le=30.0, description="Max 30 pts")
    funding_suitability_score: float = Field(ge=0.0, le=25.0, description="Max 25 pts")
    academic_subject_fit_score: float = Field(ge=0.0, le=15.0, description="Max 15 pts")
    skills_project_relevance_score: float = Field(ge=0.0, le=10.0, description="Max 10 pts")
    preferred_country_fit_score: float = Field(ge=0.0, le=10.0, description="Max 10 pts")
    deadline_readiness_score: float = Field(ge=0.0, le=10.0, description="Max 10 pts")
    score_breakdown: Dict[str, str] = Field(default_factory=dict)
    reason: str = ""
    uncertainties: List[str] = Field(default_factory=list)

# =====================================================================
# Opportunity Schema
# =====================================================================

class Opportunity(BaseModel):
    """A distinct postgraduate program or scholarship opportunity."""
    id: str
    name: str = Field(description="Program or scholarship exact name")
    university_or_provider: str
    country: str
    degree_level: str
    subject_area: str
    citizenship_restrictions: List[str] = Field(default_factory=list)
    academic_eligibility_reqs: str = ""
    language_requirements: str = ""
    funding_amount: str = ""
    funding_type: Literal[
        "Full Tuition + Living Stipend",
        "Full Tuition",
        "Substantial Partial Scholarship",
        "Merit Award",
        "Need-based Aid / Fee Waiver",
        "Self-funded / Partial"
    ] = "Full Tuition + Living Stipend"
    application_type: Literal[
        "Automatic with admission",
        "Separate scholarship application",
        "Nomination required"
    ] = "Separate scholarship application"
    deadline: str = "TBD / Rolling"
    deadline_status: Literal[
        "open",
        "upcoming_not_open",
        "closed",
        "rolling_admissions",
        "unknown",
        "extended_pending_verification",
        "rolling",
        "future"
    ] = "open"
    target_intake: str = "Fall 2026"
    required_documents: List[str] = Field(default_factory=list)
    official_url: str
    application_url: Optional[str] = None
    source_evidence: List[SourceEvidence] = Field(default_factory=list)
    eligibility: Optional[EligibilityAssessment] = None
    match_score: Optional[MatchScore] = None
    retrieval_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    is_cached: bool = False

# =====================================================================
# Agent Events, Drafting & Workflow Schemas
# =====================================================================

class AgentEvent(BaseModel):
    """Real-time observability log entry for agent actions."""
    agent_name: str
    action: str
    status: Literal["started", "in_progress", "completed", "warning", "failed"]
    detail: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().strftime("%H:%M:%S"))

class ApplicationDraft(BaseModel):
    """Personalized statement of purpose or application draft."""
    opportunity_id: str
    opportunity_name: str
    university: str
    document_type: str = "Statement of Purpose"
    content: str
    personalization_checklist: List[str] = Field(default_factory=list)
    verified_facts_used: List[str] = Field(default_factory=list)
    unverified_claims_avoided: List[str] = Field(default_factory=list)
    generated_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class WorkflowResult(BaseModel):
    """Comprehensive result of an end-to-end coordinator execution."""
    run_id: str
    student_profile: StudentProfile
    discovered_candidates: List[Opportunity] = Field(default_factory=list)
    verified_opportunities: List[Opportunity] = Field(default_factory=list)
    top_recommendations: List[Opportunity] = Field(default_factory=list)
    execution_log: List[AgentEvent] = Field(default_factory=list)
    application_draft: Optional[ApplicationDraft] = None
    execution_time_seconds: float = 0.0
    is_demo_mode: bool = False
    warnings: List[str] = Field(default_factory=list)
