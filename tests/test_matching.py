"""
Tests for Agent 4: Scholarship Matching and Ranking Agent.
Verifies the 100-point formula, exclusion of ineligible candidates, and multi-profile adaptability.
"""
import pytest
from agents.matching_agent import MatchingAgent
from agents.eligibility_agent import EligibilityAgent
from models.schemas import StudentProfile, Opportunity, EligibilityAssessment, SourceEvidence
from data.sample_profiles import RAHUL_PROFILE, MARIA_PROFILE

@pytest.fixture
def matching_agent():
    return MatchingAgent()

def test_100_point_scoring_formula(matching_agent):
    """Verify that scoring adheres to the 100-pt formula bounds and subcomponents."""
    profile = StudentProfile(**RAHUL_PROFILE)
    opp = Opportunity(
        id="test-score",
        name="UBC Research Fellowship",
        university_or_provider="University of British Columbia",
        country="Canada",
        degree_level="Master of Science",
        subject_area="Computer Science",
        funding_type="Full Tuition + Living Stipend",
        deadline_status="open",
        official_url="https://cs.ubc.ca",
        source_evidence=[
            SourceEvidence(
                url="https://cs.ubc.ca",
                confidence_policy="official_direct",
                excerpt="Full stipend and tuition."
            )
        ],
        eligibility=EligibilityAssessment(
            status="likely_eligible",
            is_verified=True,
            explanation="Fully eligible"
        )
    )

    top_five, scored_all, _ = matching_agent.rank_opportunities([opp], profile)
    assert len(scored_all) == 1
    score = scored_all[0].match_score
    assert score is not None
    assert 0.0 <= score.total_score <= 100.0
    assert score.eligibility_evidence_score <= 30.0
    assert score.funding_suitability_score <= 25.0
    assert score.academic_subject_fit_score <= 15.0
    assert score.skills_project_relevance_score <= 10.0
    assert score.preferred_country_fit_score <= 10.0
    assert score.deadline_readiness_score <= 10.0

def test_exclusion_of_ineligible_candidates(matching_agent):
    """Verify that opportunities with not_eligible status are excluded from top recommendations."""
    profile = StudentProfile(**RAHUL_PROFILE)

    ineligible_opp = Opportunity(
        id="ineligible-1",
        name="Domestic Only Award",
        university_or_provider="Local Foundation",
        country="Canada",
        degree_level="Master of Science",
        subject_area="Computer Science",
        funding_type="Full Tuition",
        official_url="https://local.org",
        eligibility=EligibilityAssessment(
            status="not_eligible",
            conflicting_criteria=["Domestic citizens only."],
            explanation="Ineligible due to citizenship restriction.",
            is_verified=True
        )
    )

    eligible_opp = Opportunity(
        id="eligible-1",
        name="Global Scholarship",
        university_or_provider="Global Uni",
        country="Canada",
        degree_level="Master of Science",
        subject_area="Computer Science",
        funding_type="Full Tuition",
        official_url="https://global.org",
        eligibility=EligibilityAssessment(
            status="likely_eligible",
            is_verified=True,
            explanation="Meets all requirements."
        )
    )

    top_five, scored_all, _ = matching_agent.rank_opportunities([ineligible_opp, eligible_opp], profile)
    rec_ids = [o.id for o in top_five]
    assert "eligible-1" in rec_ids
    assert "ineligible-1" not in rec_ids

def test_second_student_profile_adaptation(matching_agent):
    """Verify that the matching agent adapts cleanly to Maria's different profile (Brazil, Math, 3.85 GPA)."""
    maria = StudentProfile(**MARIA_PROFILE)
    rahul = StudentProfile(**RAHUL_PROFILE)

    opp_germany = Opportunity(
        id="germany-opp",
        name="DAAD Fellowship",
        university_or_provider="DAAD",
        country="Germany",
        degree_level="Master of Science",
        subject_area="Applied Mathematics and Computational Sciences",
        funding_type="Full Tuition + Living Stipend",
        deadline_status="open",
        official_url="https://daad.de",
        eligibility=EligibilityAssessment(status="likely_eligible", is_verified=True)
    )

    opp_singapore = Opportunity(
        id="singapore-opp",
        name="SINGA Award",
        university_or_provider="A*STAR",
        country="Singapore",
        degree_level="PhD / Direct PhD",
        subject_area="Computer Science",
        funding_type="Full Tuition + Living Stipend",
        deadline_status="open",
        official_url="https://a-star.edu.sg",
        eligibility=EligibilityAssessment(status="likely_eligible", is_verified=True)
    )

    top_maria, _, _ = matching_agent.rank_opportunities([opp_germany, opp_singapore], maria)
    top_rahul, _, _ = matching_agent.rank_opportunities([opp_germany, opp_singapore], rahul)

    # Maria preferred Germany and Math; Singapore is NOT in Maria's preferred countries
    maria_scores = {o.id: o.match_score.total_score for o in top_maria}
    assert maria_scores["germany-opp"] > maria_scores["singapore-opp"]
