"""
Sample profile datasets for the AI Scholarship Finder hackathon demo.
Profile 1: Rahul Sharma (Primary reference student: BTech CS, 8.2 CGPA, AI/ML, Canada/Germany/Singapore)
Profile 2: Maria Santos (Second student profile: BSc Mathematics & Informatics, 3.85/4.0 GPA, NLP/Vision, UK/Canada/Sweden)
"""
from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent

RAHUL_PROFILE = {
    "full_name": "Rahul Sharma",
    "email": "rahul.sharma@example.edu",
    "nationality": "India",
    "current_degree": "BTech in Computer Science and Engineering",
    "major": "Computer Science",
    "cgpa": 8.2,
    "gpa_scale": 10.0,
    "expected_graduation_year": 2025,
    "skills": [
        "Python", "Machine Learning", "Deep Learning", "PyTorch",
        "Natural Language Processing", "SQL", "Git", "Docker"
    ],
    "projects": [
        "Vision-based Plant Disease Detection using Deep Convolutional Networks",
        "Multi-Agent Traffic Signal Optimization System with Deep Q-Networks",
        "End-to-End Generative AI Research Paper Summarizer"
    ],
    "github_username": "rahul-ml-dev",
    "target_degree": "Master of Science (MSc / MS)",
    "target_subject": "Computer Science / Artificial Intelligence",
    "preferred_countries": ["Canada", "Germany", "Singapore"],
    "target_intake": "Fall 2026",
    "english_test_status": "IELTS 7.5 (Academic)",
    "funding_requirement": "Full tuition and living stipend or substantial scholarship",
    "user_verified": True
}

MARIA_PROFILE = {
    "full_name": "Maria Santos",
    "email": "maria.santos@example.org",
    "nationality": "Brazil",
    "current_degree": "Bachelor of Science in Computational Mathematics",
    "major": "Applied Mathematics & Computing",
    "cgpa": 3.85,
    "gpa_scale": 4.0,
    "expected_graduation_year": 2025,
    "skills": [
        "Python", "C++", "Numerical Optimization", "TensorFlow",
        "Statistics", "Linux", "Linear Algebra", "Data Analysis"
    ],
    "projects": [
        "High-Dimensional Topological Data Analysis for Genomic Sequences",
        "Monte Carlo Simulations for Renewable Energy Grid Resilience",
        "Stochastic Gradient Descent Variant for Constrained Optimization"
    ],
    "github_username": "mariasantos-math",
    "target_degree": "Master of Science (MSc)",
    "target_subject": "Computational Sciences and Data Engineering",
    "preferred_countries": ["Germany", "Canada"],
    "target_intake": "Fall 2026",
    "english_test_status": "TOEFL iBT 105",
    "funding_requirement": "Full Tuition + Research Fellowship",
    "user_verified": True
}

def save_sample_profiles():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "rahul_profile.json", "w", encoding="utf-8") as f:
        json.dump(RAHUL_PROFILE, f, indent=2)
    with open(DATA_DIR / "maria_profile.json", "w", encoding="utf-8") as f:
        json.dump(MARIA_PROFILE, f, indent=2)

if __name__ == "__main__":
    save_sample_profiles()
    print("Sample profiles created successfully.")
