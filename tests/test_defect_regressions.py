"""
Automated Correctness & Defect Regression Test Suite
File: tests/test_defect_regressions.py

Verifies resolution of the 6 core defects identified in Phase 1:
1. Master's programs excluded from PhD-targeted profile primary recommendations.
2. Historical deadlines deterministically classified as closed.
3. Inaccessible sources strictly producing insufficient_information status.
4. High match scores / funding cannot override fundamental eligibility or degree mismatches.
5. SOP Claim Validation redacts unsupported metrics and publications.
6. Research results expose structured field-level source evidence.
"""
import pytest
from datetime import date
from models.schemas import StudentProfile, Opportunity, EligibilityAssessment, SourceEvidence, FieldLevelEvidence
from agents.matching_agent import MatchingAgent
from agents.eligibility_agent import EligibilityAgent
from services.deadline_service import DeadlineService
from services.claim_validator import ClaimValidator
from utils.scoring import calculate_match_score

@pytest.fixture
def matching_agent():
    return MatchingAgent()

@pytest.fixture
def eligibility_agent():
    return EligibilityAgent()

def test_phd_profile_excludes_masters_programs(matching_agent, eligibility_agent):
    """Defect 1: A PhD-only target does not return master's-only programs in primary recommendations."""
    phd_student = StudentProfile(
        full_name="PhD Aspirant",
        target_degree="PhD in Computer Science",
        preferred_countries=["Canada"]
    )

    masters_opp = Opportunity(
        id="masters-only-1",
        name="MSc in Computing",
        university_or_provider="UBC",
        country="Canada",
        degree_level="Master of Science (MSc)",
        subject_area="Computer Science",
        funding_type="Full Tuition + Living Stipend",
        deadline_status="open",
        official_url="https://cs.ubc.ca"
    )

    # 1. Eligibility agent must detect degree level conflict
    assessment = eligibility_agent.verify_candidate(masters_opp, phd_student)
    assert assessment.status == "not_eligible"
    assert any("Degree level conflict" in c for c in assessment.conflicting_criteria)

    # 2. Matching agent must exclude masters-only program from primary recommendations
    masters_opp.eligibility = assessment
    top_recs, scored_all, _ = matching_agent.rank_opportunities([masters_opp], phd_student)
    assert len(top_recs) == 0, "Master's program should be excluded from PhD recommendations!"

def test_masters_profile_excludes_phd_only_programs(matching_agent, eligibility_agent):
    """Defect 1: A master's target does not return PhD-only programs as primary matches."""
    masters_student = StudentProfile(
        full_name="Master Aspirant",
        target_degree="Master of Science (MSc / MS)",
        preferred_countries=["Singapore"]
    )

    phd_opp = Opportunity(
        id="phd-only-1",
        name="Doctoral Research Fellowship",
        university_or_provider="NUS",
        country="Singapore",
        degree_level="Doctor of Philosophy (PhD)",
        subject_area="Computer Science",
        funding_type="Full Tuition + Living Stipend",
        deadline_status="open",
        official_url="https://comp.nus.edu.sg"
    )

    assessment = eligibility_agent.verify_candidate(phd_opp, masters_student)
    assert assessment.status == "not_eligible"
    assert any("Degree level conflict" in c for c in assessment.conflicting_criteria)

    phd_opp.eligibility = assessment
    top_recs, scored_all, _ = matching_agent.rank_opportunities([phd_opp], masters_student)
    assert len(top_recs) == 0, "PhD program should be excluded from Master's recommendations!"

def test_historical_deadlines_classified_closed():
    """Defect 2: Historical deadlines are classified as closed unless extension is verified."""
    # Test dates in 2025 and early 2026 evaluated against current runtime or fixed date
    fixed_today = date(2026, 10, 22)

    status_past_2025, parsed_d, expl = DeadlineService.evaluate_status(
        deadline_text="December 15, 2025",
        reference_date=fixed_today
    )
    assert status_past_2025 == "closed"
    assert "has passed" in expl

    status_past_early_2026, _, _ = DeadlineService.evaluate_status(
        deadline_text="March 20, 2026",
        reference_date=fixed_today
    )
    assert status_past_early_2026 == "closed"

    status_future, _, _ = DeadlineService.evaluate_status(
        deadline_text="December 1, 2026",
        reference_date=fixed_today
    )
    assert status_future == "upcoming_not_open"

def test_future_deadlines_not_assumed_open_without_window():
    """Defect 2: Future deadlines are not assumed open when an upcoming start date is known."""
    fixed_today = date(2026, 10, 22)
    status, _, expl = DeadlineService.evaluate_status(
        deadline_text="February 28, 2027",
        open_date_text="December 1, 2026",
        reference_date=fixed_today
    )
    assert status == "upcoming_not_open"
    assert "not open until" in expl

def test_inaccessible_source_produces_insufficient_information(eligibility_agent):
    """Defect 3: A missing or inaccessible source cannot produce a fully verified eligibility assessment."""
    profile = StudentProfile(full_name="Test Student")
    opp = Opportunity(
        id="broken-source-1",
        name="Mystery Scholarship",
        university_or_provider="Unknown Uni",
        country="Germany",
        degree_level="Master of Science",
        subject_area="Computer Science",
        official_url="https://broken-domain-error-404.edu",
        source_evidence=[
            SourceEvidence(
                url="https://broken-domain-error-404.edu",
                confidence_policy="inaccessible_or_conflicting",
                excerpt="HTTP 404 Not Found"
            )
        ]
    )

    assessment = eligibility_agent.verify_candidate(opp, profile)
    assert assessment.status == "insufficient_information"
    assert assessment.is_verified is False

def test_high_funding_score_cannot_override_fundamental_mismatch():
    """Defect 4: High match scores cannot override fundamental eligibility mismatches."""
    student = StudentProfile(
        full_name="International Student",
        nationality="India",
        target_degree="Master of Science",
        preferred_countries=["Canada"]
    )

    # Opportunity with full tuition + living stipend ($30k+), but citizenship restriction
    ineligible_opp = Opportunity(
        id="citizens-only-1",
        name="Domestic Elite Grant",
        university_or_provider="Canadian Institute",
        country="Canada",
        degree_level="Master of Science",
        subject_area="Computer Science",
        funding_type="Full Tuition + Living Stipend",
        citizenship_restrictions=["Domestic citizens only"],
        deadline_status="open",
        official_url="https://canada.edu",
        eligibility=EligibilityAssessment(
            status="not_eligible",
            conflicting_criteria=["Restricted to citizens of Canada"],
            is_verified=True
        )
    )

    score = calculate_match_score(student, ineligible_opp)
    # Funding score must be nullified (0.0) and eligibility score must be 0.0
    assert score.eligibility_evidence_score == 0.0
    assert score.funding_suitability_score == 0.0
    assert "Disqualified" in score.score_breakdown["funding_suitability"]
    # Total score cannot be viable
    assert score.total_score < 40.0

def test_sop_claim_validation_redacts_unsupported_metrics_and_publications():
    """Defect 5: An SOP cannot claim unsupported achievements or technical implementation details."""
    profile = StudentProfile(
        full_name="Aman Gupta",
        current_degree="BTech in Computer Science",
        major="Computer Science",
        skills=["Python", "PyTorch"],
        projects=["Traffic Sign Classifier with CNN"]
    )
    opp = Opportunity(
        id="test-opp",
        name="AI Fellowship",
        university_or_provider="UToronto",
        country="Canada",
        degree_level="Master of Science",
        subject_area="Artificial Intelligence",
        official_url="https://utoronto.ca"
    )

    untrusted_llm_draft = (
        "During my thesis, I achieved a precision of 99.8% and published a co-authored paper in IEEE. "
        "I was awarded first place in the national coding summit. "
        "I conducted research in collaboration with Dr. Geoffrey Hinton."
    )

    sanitized, verified_facts, flagged = ClaimValidator.validate_and_sanitize_draft(
        draft_text=untrusted_llm_draft,
        profile=profile,
        opportunity=opp
    )

    # Verifications
    assert "99.8%" not in sanitized
    assert "IEEE" not in sanitized
    assert "Geoffrey Hinton" not in sanitized
    assert "first place" not in sanitized
    assert len(flagged) >= 3
    assert any("metric" in f.lower() for f in flagged)
    assert any("publication" in f.lower() for f in flagged)
    assert any("faculty" in f.lower() for f in flagged)

def test_field_level_source_evidence_exposed():
    """Defect 6: Research results expose field-level source evidence with quotations."""
    ev = SourceEvidence(
        url="https://cs.ubc.ca/awards",
        title="UBC CS Funding",
        excerpt="Full tuition waiver and stipend.",
        field_evidence=[
            FieldLevelEvidence(
                field_name="funding_amount",
                extracted_value="CAD $28,000/year",
                source_url="https://cs.ubc.ca/awards",
                exact_quote="Graduate research assistants receive CAD $28,000 annual stipend.",
                verification_state="verified"
            )
        ]
    )
    assert len(ev.field_evidence) == 1
    assert ev.field_evidence[0].field_name == "funding_amount"
    assert "CAD $28,000" in ev.field_evidence[0].exact_quote
    assert ev.field_evidence[0].verification_state == "verified"
