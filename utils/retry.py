"""
Retry utility with bounded exponential backoff for resilient API requests.
"""
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import requests

logger = logging.getLogger(__name__)

# Standard network exceptions for safe retries
RETRYABLE_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.HTTPError,
)

def make_bounded_retry(
    max_attempts: int = 3,
    min_wait_seconds: float = 1.0,
    max_wait_seconds: float = 8.0,
):
    """Factory creating a tenacity retry decorator with bounded backoff."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=min_wait_seconds, min=min_wait_seconds, max=max_wait_seconds),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
