"""
Tests for Agent 2: Scholarship and Program Discovery Agent.
Verifies discovery of >= 10 candidates, deduplication, and source URL persistence.
"""
import pytest
from agents.discovery_agent import DiscoveryAgent
from models.schemas import StudentProfile

def test_discovery_candidates_count():
    """Verify discovery produces at least 10 candidates with valid official URLs."""
    agent = DiscoveryAgent()
    profile = StudentProfile(
        full_name="Rahul Sharma",
        preferred_countries=["Canada", "Germany", "Singapore"]
    )
    events = []
    candidates = agent.discover(profile, events_collector=events)

    assert len(candidates) >= 10
    for cand in candidates:
        assert cand.id
        assert cand.name
        assert cand.university_or_provider
        assert cand.country
        assert cand.official_url.startswith("http")
        assert len(cand.source_evidence) > 0

def test_discovery_deduplication():
    """Verify that duplicate candidate programs are purged."""
    agent = DiscoveryAgent()
    profile = StudentProfile(preferred_countries=["Canada"])
    candidates = agent.discover(profile)

    keys = [f"{c.university_or_provider.lower()}::{c.name.lower()}" for c in candidates]
    assert len(keys) == len(set(keys)), "Duplicate university-program pairs detected!"

def test_discovery_country_prioritization():
    """Verify that opportunities in preferred countries are prioritized."""
    agent = DiscoveryAgent()
    profile = StudentProfile(preferred_countries=["Singapore"])
    candidates = agent.discover(profile)

    # First candidate should match preferred country
    assert candidates[0].country == "Singapore"
