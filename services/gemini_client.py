"""
Gemini API client using the current official google-genai Python SDK.
Provides structured LLM reasoning and Google Search grounding.
Distinguishes strictly between live calls and transparent demonstration fallbacks.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from google import genai
from google.genai import types

from config import AppConfig
from utils.retry import make_bounded_retry

logger = logging.getLogger(__name__)

class GeminiClient:
    """Wrapper around the Google GenAI SDK with graceful fallbacks and search grounding."""

    def __init__(self):
        self.api_key = AppConfig.GEMINI_API_KEY
        self.model_name = AppConfig.GEMINI_MODEL
        self._client: Optional[genai.Client] = None

        if AppConfig.is_live_gemini_available():
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self._client = None

    @property
    def is_live(self) -> bool:
        """Indicates if live client is configured with active credentials."""
        return self._client is not None

    def test_connection(self) -> Dict[str, Any]:
        """Runs a minimal non-sensitive request to verify credentials."""
        if not self.is_live:
            return {
                "success": False,
                "error": "No valid GEMINI_API_KEY configured in environment or .env",
                "is_live": False
            }
        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents="Ping. Respond with 'PONG' only."
            )
            return {
                "success": True,
                "response": response.text.strip() if response.text else "PONG",
                "model": self.model_name,
                "is_live": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Gemini API authentication/connection failed: {str(e)[:120]}",
                "is_live": False
            }

    def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        enable_grounding: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes generation with optional search grounding.
        If live API is unavailable, returns explicit demonstration fallback.
        """
        if not self.is_live:
            return {
                "success": True,
                "text": "",
                "is_live": False,
                "is_demo": True,
                "notice": "DEMONSTRATION MODE: GEMINI_API_KEY not configured. Set GEMINI_API_KEY in .env for live AI reasoning."
            }

        try:
            tools = [types.Tool(google_search=types.GoogleSearch())] if enable_grounding else None
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
                tools=tools
            )

            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            grounding_chunks = []
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
                    metadata = candidate.grounding_metadata
                    if hasattr(metadata, "grounding_chunks") and metadata.grounding_chunks:
                        for chunk in metadata.grounding_chunks:
                            if hasattr(chunk, "web") and chunk.web:
                                grounding_chunks.append({
                                    "title": getattr(chunk.web, "title", ""),
                                    "uri": getattr(chunk.web, "uri", "")
                                })

            return {
                "success": True,
                "text": response.text or "",
                "is_live": True,
                "is_demo": False,
                "grounding_sources": grounding_chunks
            }

        except Exception as e:
            logger.error(f"Gemini API error during generation: {e}")
            return {
                "success": False,
                "error": str(e),
                "is_live": False,
                "is_demo": True,
                "notice": f"Live Gemini API error: {str(e)[:100]}. Falling back to verified static evidence."
            }
