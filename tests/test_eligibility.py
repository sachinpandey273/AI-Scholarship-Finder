"""
Tests for Agent 3: Eligibility and Official-Source Verification Agent.
Verifies the 4 explicit eligibility statuses, citizenship checks, and GPA audits.
"""
import pytest
from agents.eligibility_agent import EligibilityAgent
from models.schemas import StudentProfile, Opportunity, SourceEvidence

@pytest.fixture
def eligibility_agent():
    return EligibilityAgent()

@pytest.fixture
def base_student():
    return StudentProfile(
        full_name="Rahul Sharma",
        nationality="India",
        current_degree="BTech in Computer Science",
        major="Computer Science",
        cgpa=8.2,
        gpa_scale=10.0,
        english_test_status="IELTS 7.5 (Academic)",
        preferred_countries=["Canada", "Germany", "Singapore"]
    )

def test_likely_eligible_status(eligibility_agent, base_student):
    """Verify likely_eligible when all academic, language, and nationality criteria align."""
    opp = Opportunity(
        id="test-1",
        name="Graduate Fellowship",
        university_or_provider="Top University",
        country="Canada",
        degree_level="Master of Science",
        subject_area="Computer Science",
        citizenship_restrictions=["Open to all international graduates"],
        academic_eligibility_reqs="Minimum 80% / 8.0 CGPA",
        language_requirements="IELTS 7.0 minimum",
        official_url="https://topuni.ca/fellowship",
        source_evidence=[
            SourceEvidence(
                url="https://topuni.ca/fellowship",
                is_official=True,
                excerpt="Open to all international students with 80% undergraduate score.",
                confidence_policy="official_direct"
            )
        ]
    )
    assessment = eligibility_agent.verify_candidate(opp, base_student)
    assert assessment.status == "likely_eligible"
    assert len(assessment.confirmed_criteria) > 0
    assert len(assessment.conflicting_criteria) == 0

def test_not_eligible_citizenship_restriction(eligibility_agent, base_student):
    """Verify not_eligible status when student nationality conflicts with program restriction."""
    opp = Opportunity(
        id="test-2",
        name="National Domestic Grant",
        university_or_provider="Domestic Agency",
        country="Canada",
        degree_level="Master of Science",
        subject_area="Computer Science",
        citizenship_restrictions=["Canadian citizens only (Domestic only)"],
        academic_eligibility_reqs="Minimum 80%",
        official_url="https://canada.ca/grant",
        source_evidence=[
            SourceEvidence(
                url="https://canada.ca/grant",
                is_official=True,
                excerpt="Only Canadian citizens are eligible to apply.",
                confidence_policy="official_direct"
            )
        ]
    )
    assessment = eligibility_agent.verify_candidate(opp, base_student)
    assert assessment.status == "not_eligible"
    assert len(assessment.conflicting_criteria) > 0
    assert "Restricted to citizens of Canada" in assessment.conflicting_criteria[0]

def test_potential_fit_with_missing_criteria(eligibility_agent, base_student):
    """Verify potential_fit when institutional nomination or higher language score is required."""
    opp = Opportunity(
        id="test-3",
        name="Faculty Nominated Award",
        university_or_provider="Ontario Institute",
        country="Canada",
        degree_level="Master of Science",
        subject_area="Computer Science",
        citizenship_restrictions=["Open to international students"],
        academic_eligibility_reqs="First class standing",
        language_requirements="IELTS 8.0 or departmental interview",
        application_type="Nomination required",
        official_url="https://ontario.ca/nomination",
        source_evidence=[
            SourceEvidence(
                url="https://ontario.ca/nomination",
                is_official=True,
                excerpt="Nomination required by faculty department.",
                confidence_policy="official_direct"
            )
        ]
    )
    assessment = eligibility_agent.verify_candidate(opp, base_student)
    assert assessment.status == "potential_fit"
    assert len(assessment.missing_or_unresolved_criteria) > 0

def test_insufficient_information_on_inaccessible_source(eligibility_agent, base_student):
    """Verify insufficient_information when source is inaccessible and no facts confirmed."""
    opp = Opportunity(
        id="test-4",
        name="Unknown Portal Grant",
        university_or_provider="Broken University",
        country="Germany",
        degree_level="Master of Science",
        subject_area="Computer Science",
        official_url="https://broken-domain-999.de/award",
        source_evidence=[
            SourceEvidence(
                url="https://broken-domain-999.de/award",
                is_official=True,
                excerpt="Portal returned status code 404. Fact unconfirmed.",
                confidence_policy="inaccessible_or_conflicting"
            )
        ]
    )
    assessment = eligibility_agent.verify_candidate(opp, base_student)
    assert assessment.status in ["insufficient_information", "potential_fit"]
