"""
Configuration settings for the AI Scholarship Finder.
Handles environment variables safely without exposing secrets.
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load local .env if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class AppConfig:
    """Application configuration and credentials validation."""

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "").strip()

    CACHE_DIR: Path = BASE_DIR / os.getenv("CACHE_DIR", "data/cache")
    UPLOAD_DIR: Path = BASE_DIR / os.getenv("UPLOAD_DIR", "data/uploads")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Request timeouts & retries
    DEFAULT_TIMEOUT_SECONDS: int = 15
    MAX_RETRIES: int = 3
    BACKOFF_FACTOR: float = 1.5

    @classmethod
    def initialize_directories(cls) -> None:
        """Ensure necessary storage directories exist."""
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def is_live_gemini_available(cls) -> bool:
        """Check if a non-placeholder Gemini API key is configured."""
        return bool(cls.GEMINI_API_KEY and not cls.GEMINI_API_KEY.startswith("your_"))

    @classmethod
    def is_github_token_available(cls) -> bool:
        """Check if a non-placeholder GitHub token is configured."""
        return bool(cls.GITHUB_TOKEN and not cls.GITHUB_TOKEN.startswith("optional_"))

    @classmethod
    def get_censored_key_preview(cls, key: str) -> str:
        """Return safe censored preview like 'AIza...8f2' without revealing secret."""
        if not key or len(key) < 8:
            return "[Not Set]"
        return f"{key[:4]}...{key[-3:]}"

# Initialize storage dirs on import
AppConfig.initialize_directories()
