"""
GitHub profile and repository enrichment service.
Fetches public GitHub profiles and repositories without requiring authentication by default.
Handles invalid usernames, rate limits, and network errors gracefully.
"""
from __future__ import annotations

import re
from typing import Dict, Any, List, Optional
import requests
from config import AppConfig
from models.schemas import StudentEvidence
from utils.retry import make_bounded_retry

class GitHubService:
    """Service for enriching student profile via GitHub REST API."""

    BASE_URL = "https://api.github.com"

    @classmethod
    def clean_username(cls, username_or_url: str) -> str:
        """Extract clean username from a URL or raw string."""
        if not username_or_url:
            return ""
        text = username_or_url.strip()
        match = re.search(r'(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_-]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text.strip().lstrip("@")

    @classmethod
    def _get_headers(cls) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Scholarship-Finder/1.0",
        }
        if AppConfig.is_github_token_available():
            headers["Authorization"] = f"Bearer {AppConfig.GITHUB_TOKEN}"
        return headers

    @classmethod
    def fetch_user_profile(cls, username_or_url: str) -> Dict[str, Any]:
        """
        Fetch public user profile and recent repositories.
        Does not require a token for public access.
        """
        username = cls.clean_username(username_or_url)
        if not username:
            return {
                "success": False,
                "error": "No GitHub username provided",
                "evidence": []
            }

        headers = cls._get_headers()
        session = requests.Session()

        try:
            # 1. Fetch user metadata
            user_resp = session.get(
                f"{cls.BASE_URL}/users/{username}",
                headers=headers,
                timeout=AppConfig.DEFAULT_TIMEOUT_SECONDS
            )

            if user_resp.status_code == 404:
                return {
                    "success": False,
                    "error": f"GitHub user '{username}' not found (HTTP 404).",
                    "username": username,
                    "evidence": []
                }
            elif user_resp.status_code == 403:
                return {
                    "success": False,
                    "error": "GitHub API rate limit exceeded. Public rate limit applies.",
                    "username": username,
                    "evidence": []
                }
            elif user_resp.status_code != 200:
                return {
                    "success": False,
                    "error": f"GitHub API returned HTTP {user_resp.status_code}",
                    "username": username,
                    "evidence": []
                }

            user_data = user_resp.json()

            # 2. Fetch public repos
            repos_resp = session.get(
                f"{cls.BASE_URL}/users/{username}/repos?sort=updated&per_page=10",
                headers=headers,
                timeout=AppConfig.DEFAULT_TIMEOUT_SECONDS
            )

            repos_list = repos_resp.json() if repos_resp.status_code == 200 else []

            # 3. Extract projects, languages, and topics
            projects_summary = []
            detected_languages = set()

            for repo in repos_list:
                if isinstance(repo, dict):
                    name = repo.get("name", "")
                    desc = repo.get("description", "") or "No description"
                    lang = repo.get("language")
                    stars = repo.get("stargazers_count", 0)
                    topics = repo.get("topics", [])

                    if lang:
                        detected_languages.add(lang)
                    for t in topics:
                        detected_languages.add(t)

                    proj_str = f"{name}: {desc} (Language: {lang or 'N/A'}, Stars: {stars})"
                    projects_summary.append(proj_str)

            evidence_items: List[StudentEvidence] = []
            evidence_items.append(
                StudentEvidence(
                    field_name="github_username",
                    value=username,
                    source_type="github",
                    source_reference=f"https://github.com/{username}",
                    confidence=1.0,
                    extraction_note=f"Verified public GitHub profile with {user_data.get('public_repos', 0)} repos"
                )
            )

            if detected_languages:
                evidence_items.append(
                    StudentEvidence(
                        field_name="skills",
                        value=sorted(list(detected_languages)),
                        source_type="github",
                        source_reference=f"https://github.com/{username}",
                        confidence=0.90,
                        extraction_note="Languages and topics identified from active public repositories"
                    )
                )

            if projects_summary:
                evidence_items.append(
                    StudentEvidence(
                        field_name="projects",
                        value=projects_summary[:5],
                        source_type="github",
                        source_reference=f"https://github.com/{username}?tab=repositories",
                        confidence=0.95,
                        extraction_note=f"Retrieved {len(projects_summary[:5])} top public repositories"
                    )
                )

            return {
                "success": True,
                "username": username,
                "name": user_data.get("name") or username,
                "bio": user_data.get("bio", ""),
                "public_repos_count": user_data.get("public_repos", 0),
                "repos_summary": "\n".join(projects_summary[:5]),
                "languages": sorted(list(detected_languages)),
                "evidence": evidence_items
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to retrieve GitHub profile: {str(e)}",
                "username": username,
                "evidence": []
            }
