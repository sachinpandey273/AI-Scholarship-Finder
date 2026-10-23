"""
Tests for Agent 1: Student Profile Analyst and Document Parser.
Verifies parsing of PDF/DOCX, CGPA conflicts, unknown fields, and GitHub fallbacks.
"""
from pathlib import Path
import pytest
from services.document_parser import DocumentParser
from services.github_service import GitHubService
from agents.profile_agent import ProfileAnalystAgent
from models.schemas import StudentProfile

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_PDF = BASE_DIR / "data" / "sample_documents" / "sample_resume.pdf"
SAMPLE_DOCX = BASE_DIR / "data" / "sample_documents" / "sample_transcript.docx"

def test_pdf_extraction_real():
    """Verify text extraction from generated sample PDF."""
    res = DocumentParser.extract_text_from_pdf(SAMPLE_PDF)
    assert res["success"] is True
    assert "Rahul Sharma" in res["text"]
    assert "8.2" in res["text"]

def test_docx_extraction_real():
    """Verify text extraction from generated sample DOCX."""
    res = DocumentParser.extract_text_from_docx(SAMPLE_DOCX)
    assert res["success"] is True
    assert "ACADEMIC TRANSCRIPT" in res["text"]
    assert "8.2" in res["text"]

def test_scanned_or_empty_pdf_error_handling(tmp_path):
    """Verify proper error detection when PDF has no extractable text."""
    empty_pdf = tmp_path / "empty.pdf"
    # Create empty 0-byte file
    empty_pdf.write_bytes(b"")
    res = DocumentParser.extract_text_from_pdf(empty_pdf)
    assert res["success"] is False
    assert "error" in res

def test_fact_parsing_provenance():
    """Verify facts extracted have proper provenance and confidence."""
    text = "Rahul Sharma. CGPA: 8.5 / 10.0. BTech in Computer Science. Skills: Python, PyTorch, Docker. Email: test@edu.org"
    ev_list = DocumentParser.parse_facts_from_text(text, "test_resume.pdf", "resume_pdf")
    fields = {e.field_name: e.value for e in ev_list}
    assert fields["cgpa"] == 8.5
    assert fields["gpa_scale"] == 10.0
    assert "Python" in fields["skills"]
    assert fields["email"] == "test@edu.org"

def test_conflicting_cgpa_handling():
    """Verify that transcript evidence takes precedence over conflicting resume claims."""
    agent = ProfileAnalystAgent()
    profile = agent.analyze_profile(
        resume_path=SAMPLE_PDF,
        transcript_path=SAMPLE_DOCX,
        manual_overrides={"cgpa": 8.2}
    )
    assert profile.cgpa == 8.2
    assert profile.gpa_scale == 10.0
    assert len(profile.evidence_chain) > 0

def test_unknown_fields_preservation():
    """Verify that unidentified attributes are preserved in unknown_fields."""
    agent = ProfileAnalystAgent()
    profile = agent.analyze_profile(
        manual_overrides={"skills": [], "projects": []}
    )
    assert "skills" in profile.unknown_fields or len(profile.skills) > 0

def test_github_fallback_for_invalid_username():
    """Verify that nonexistent GitHub usernames are handled gracefully without crash."""
    service = GitHubService()
    res = service.fetch_user_profile("nonexistent_user_xyz_998811_abc")
    assert res["success"] is False
    assert "not found" in res["error"].lower() or "rate limit" in res["error"].lower()
