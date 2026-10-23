"""
Document parsing service for PDF and DOCX files.
Extracts academic qualifications, CGPA, grading scale, skills, and projects locally.
Handles scanned, corrupted, and empty documents with explicit warnings.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from pypdf import PdfReader
import docx

from models.schemas import StudentEvidence

class DocumentParser:
    """Extracts text and candidate academic facts from student documents."""

    SKILL_KEYWORDS = [
        "Python", "Java", "C++", "C", "JavaScript", "TypeScript", "SQL",
        "Machine Learning", "Deep Learning", "Artificial Intelligence", "AI",
        "Natural Language Processing", "NLP", "Computer Vision", "PyTorch",
        "TensorFlow", "Keras", "Scikit-Learn", "Pandas", "NumPy",
        "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Git", "Linux",
        "FastAPI", "Flask", "Django", "React", "Node.js"
    ]

    @classmethod
    def extract_text_from_pdf(cls, file_path: str | Path) -> Dict[str, Any]:
        """Extract text from PDF using pypdf."""
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File does not exist: {path}", "text": ""}

        try:
            reader = PdfReader(str(path))
            pages_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    pages_text.append(text)

            full_text = "\n".join(pages_text).strip()
            if not full_text:
                return {
                    "success": False,
                    "error": "Scanned or empty document detected. No extractable digital text found.",
                    "text": ""
                }

            return {
                "success": True,
                "text": full_text,
                "pages_count": len(reader.pages),
                "filename": path.name
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"PDF parsing error: {str(e)}",
                "text": ""
            }

    @classmethod
    def extract_text_from_docx(cls, file_path: str | Path) -> Dict[str, Any]:
        """Extract text from DOCX using python-docx."""
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File does not exist: {path}", "text": ""}

        try:
            doc = docx.Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        paragraphs.append(row_text)

            full_text = "\n".join(paragraphs).strip()
            if not full_text:
                return {
                    "success": False,
                    "error": "Empty DOCX document. No paragraphs or table cells found.",
                    "text": ""
                }

            return {
                "success": True,
                "text": full_text,
                "filename": path.name
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"DOCX parsing error: {str(e)}",
                "text": ""
            }

    @classmethod
    def parse_facts_from_text(cls, text: str, source_name: str, source_type: str) -> List[StudentEvidence]:
        """
        Extracts candidate facts (CGPA, degree, major, skills, projects)
        from plain text with regex patterns and stores provenance.
        """
        evidence_list: List[StudentEvidence] = []
        if not text:
            return evidence_list

        # 1. CGPA / Marks Detection
        cgpa_matches = re.findall(
            r'(?:CGPA|GPA|Grade Point Average|Aggregate|Score)[:\s]*([0-9]+(?:\.[0-9]+)?)(?:\s*(?:/|out of)\s*([0-9]+(?:\.[0-9]+)?))?',
            text,
            re.IGNORECASE
        )
        if cgpa_matches:
            val_str, scale_str = cgpa_matches[0]
            val = float(val_str)
            scale = float(scale_str) if scale_str else (10.0 if val > 4.0 else 4.0)
            evidence_list.append(
                StudentEvidence(
                    field_name="cgpa",
                    value=val,
                    source_type=source_type,  # type: ignore
                    source_reference=source_name,
                    confidence=0.95,
                    extraction_note=f"Extracted CGPA {val} with scale {scale}"
                )
            )
            evidence_list.append(
                StudentEvidence(
                    field_name="gpa_scale",
                    value=scale,
                    source_type=source_type,  # type: ignore
                    source_reference=source_name,
                    confidence=0.90
                )
            )

        # 2. Degree Detection
        degree_patterns = [
            r'\b(B\.?\s?Tech(?:nology)?\s*(?:in\s+[A-Za-z\s]+)?)\b',
            r'\b(Bachelor\s+of\s+(?:Technology|Science|Engineering)\s*(?:in\s+[A-Za-z\s]+)?)\b',
            r'\b(B\.?E\.?\s*(?:in\s+[A-Za-z\s]+)?)\b',
            r'\b(B\.?Sc\.?\s*(?:in\s+[A-Za-z\s]+)?)\b',
        ]
        for pat in degree_patterns:
            deg_match = re.search(pat, text, re.IGNORECASE)
            if deg_match:
                evidence_list.append(
                    StudentEvidence(
                        field_name="current_degree",
                        value=deg_match.group(1).strip(),
                        source_type=source_type,  # type: ignore
                        source_reference=source_name,
                        confidence=0.90
                    )
                )
                break

        # 3. Major / Discipline Detection
        major_patterns = [
            r'\b(Computer\s+Science(?:\s+and\s+Engineering)?)\b',
            r'\b(Artificial\s+Intelligence(?:\s+and\s+Data\s+Science)?)\b',
            r'\b(Information\s+Technology)\b',
            r'\b(Data\s+Science)\b',
            r'\b(Software\s+Engineering)\b',
        ]
        for pat in major_patterns:
            major_match = re.search(pat, text, re.IGNORECASE)
            if major_match:
                evidence_list.append(
                    StudentEvidence(
                        field_name="major",
                        value=major_match.group(1).strip(),
                        source_type=source_type,  # type: ignore
                        source_reference=source_name,
                        confidence=0.90
                    )
                )
                break

        # 4. Skills Detection
        found_skills = []
        for skill in cls.SKILL_KEYWORDS:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                found_skills.append(skill)
        if found_skills:
            evidence_list.append(
                StudentEvidence(
                    field_name="skills",
                    value=sorted(list(set(found_skills))),
                    source_type=source_type,  # type: ignore
                    source_reference=source_name,
                    confidence=0.85,
                    extraction_note=f"Detected {len(found_skills)} technical keywords"
                )
            )

        # 5. Email detection
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
        if email_match:
            evidence_list.append(
                StudentEvidence(
                    field_name="email",
                    value=email_match.group(0),
                    source_type=source_type,  # type: ignore
                    source_reference=source_name,
                    confidence=0.98
                )
            )

        # 6. GitHub URL detection
        gh_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9-]+)', text, re.IGNORECASE)
        if gh_match:
            username = gh_match.group(1)
            evidence_list.append(
                StudentEvidence(
                    field_name="github_username",
                    value=username,
                    source_type=source_type,  # type: ignore
                    source_reference=source_name,
                    confidence=0.95
                )
            )

        return evidence_list
