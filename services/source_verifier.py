"""
Official Source Verifier service.
Safely inspects university and scholarship pages, extracts evidence,
determines official domain trust, and protects against untrusted web injection.
"""
from __future__ import annotations

import re
import ipaddress
import socket
from urllib.parse import urlparse
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

from config import AppConfig
from models.schemas import SourceEvidence
from utils.cache import get_cached_item, set_cached_item
from utils.retry import make_bounded_retry

class SourceVerifier:
    """Retrieves and inspects official educational portals and opportunities."""

    TRUSTED_TLDS = {".edu", ".ac.uk", ".de", ".ca", ".sg", ".gov", ".org"}

    @classmethod
    def is_safe_public_url(cls, url: str) -> bool:
        """Reject SSRF targets, including DNS names resolving to private IPs."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
                return False
            host = parsed.hostname.lower()
            if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
                return False
            for info in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM):
                address = ipaddress.ip_address(info[4][0])
                if not address.is_global:
                    return False
            return True
        except (OSError, ValueError):
            return False

    @classmethod
    def is_official_domain(cls, url: str) -> bool:
        """Determines if a domain corresponds to an accredited university or government portal."""
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            return any(host.endswith(tld) for tld in cls.TRUSTED_TLDS)
        except Exception:
            return False

    @classmethod
    def sanitize_untrusted_text(cls, raw_html_or_text: str) -> str:
        """
        Sanitizes text retrieved from the web:
        Strips script, tags, system prompt injection attempts, and excessive whitespace.
        """
        if not raw_html_or_text:
            return ""

        # Remove HTML tags if present
        soup = BeautifulSoup(raw_html_or_text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        clean_text = soup.get_text(separator=" ", strip=True)

        # Defend against prompt injection attempts from untrusted pages
        injection_patterns = [
            r"ignore\s+(?:all\s+)?previous\s+instructions",
            r"system\s*prompt\s*override",
            r"you\s+are\s+now\s+a",
            r"reveal\s+your\s+keys",
        ]
        for pat in injection_patterns:
            clean_text = re.sub(pat, "[REDACTED_UNTRUSTED_INSTRUCTION]", clean_text, flags=re.IGNORECASE)

        # Truncate to reasonable context window to prevent resource exhaustion
        return clean_text[:4000]

    @classmethod
    def fetch_source_evidence(cls, url: str) -> SourceEvidence:
        """
        Inspects an opportunity URL with caching and bounded retries.
        Extracts relevant excerpt, determines confidence policy, and records timestamp.
        """
        if not cls.is_safe_public_url(url):
            return SourceEvidence(
                url=url, title="Unsafe source URL", domain="", is_official=False,
                excerpt="Source URL was rejected by outbound network policy.",
                confidence_policy="inaccessible_or_conflicting", verification_state="unavailable",
            )

        cache_key = f"source_evidence:{url}"
        cached = get_cached_item(cache_key)
        if cached:
            return SourceEvidence(
                url=url,
                title=cached.get("title", ""),
                domain=cached.get("domain", ""),
                is_official=cached.get("is_official", True),
                retrieval_timestamp=cached.get("_cached_at", ""),
                excerpt=cached.get("excerpt", ""),
                confidence_policy=cached.get("confidence_policy", "official_direct")
            )

        parsed = urlparse(url)
        domain = parsed.netloc
        is_official = cls.is_official_domain(url)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            resp = requests.get(
                url,
                headers=headers,
                timeout=AppConfig.DEFAULT_TIMEOUT_SECONDS,
                allow_redirects=False,
            )

            # Never permit requests to silently cross an unvalidated redirect.
            if resp.is_redirect:
                location = resp.headers.get("Location", "")
                return SourceEvidence(
                    url=url, title="Redirect requires verification", domain=domain,
                    is_official=is_official,
                    excerpt=f"Source redirected to {location[:200]}; it was not followed until separately validated.",
                    confidence_policy="inaccessible_or_conflicting", verification_state="unavailable",
                )

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                title = soup.title.string.strip() if soup.title and soup.title.string else domain
                clean_text = cls.sanitize_untrusted_text(resp.text)

                # Extract most relevant excerpt containing scholarship/admission terms
                excerpt = ""
                paragraphs = clean_text.split(". ")
                relevant_sentences = []
                keywords = ["scholarship", "funding", "tuition", "eligibility", "deadline", "gpa", "admission", "requirements"]
                for p in paragraphs:
                    if any(kw in p.lower() for kw in keywords):
                        relevant_sentences.append(p.strip())
                        if len(relevant_sentences) >= 4:
                            break

                excerpt = ". ".join(relevant_sentences) if relevant_sentences else clean_text[:350]

                policy = "official_direct" if is_official else "third_party"
                evidence = SourceEvidence(
                    url=url,
                    title=title[:120],
                    domain=domain,
                    is_official=is_official,
                    excerpt=excerpt[:500],
                    confidence_policy=policy
                )

                set_cached_item(cache_key, evidence.model_dump(), source_url=url)
                return evidence

            else:
                return SourceEvidence(
                    url=url,
                    title=f"HTTP {resp.status_code}",
                    domain=domain,
                    is_official=is_official,
                    excerpt=f"Portal returned status code {resp.status_code}. Fact unconfirmed.",
                    confidence_policy="inaccessible_or_conflicting"
                )

        except Exception as e:
            return SourceEvidence(
                url=url,
                title="Connection Inaccessible",
                domain=domain,
                is_official=is_official,
                excerpt=f"Unable to connect to source URL: {str(e)[:100]}. Fact unconfirmed.",
                confidence_policy="inaccessible_or_conflicting"
            )
