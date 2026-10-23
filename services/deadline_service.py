"""
Canonical Deadline Service
File: services/deadline_service.py

Provides deterministic date parsing and application-cycle classification
against the current runtime date (or a frozen clock for testing).
Never asks an LLM to decide whether a date is in the past.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone, date
from typing import Optional, Tuple, Literal

DeadlineStatusType = Literal[
    "open",
    "upcoming_not_open",
    "closed",
    "rolling_admissions",
    "unknown",
    "extended_pending_verification"
]

class DeadlineService:
    """Deterministic deadline parsing, validation, and intake assessment."""

    MONTHS = {
        "january": 1, "jan": 1,
        "february": 2, "feb": 2,
        "march": 3, "mar": 3,
        "april": 4, "apr": 4,
        "may": 5,
        "june": 6, "jun": 6,
        "july": 7, "jul": 7,
        "august": 8, "aug": 8,
        "september": 9, "sep": 9, "sept": 9,
        "october": 10, "oct": 10,
        "november": 11, "nov": 11,
        "december": 12, "dec": 12,
    }

    @classmethod
    def get_current_date(cls, reference_date: Optional[date] = None) -> date:
        """Returns the current reference date in UTC, or the injected frozen date for tests."""
        if reference_date is not None:
            return reference_date
        return datetime.now(timezone.utc).date()

    @classmethod
    def parse_deadline_text(cls, deadline_text: str) -> Optional[date]:
        """
        Extracts a concrete calendar date from natural strings like:
          - 'December 15, 2025'
          - 'March 20, 2026'
          - '2026-05-31'
          - '15 October 2025'
        """
        if not deadline_text:
            return None

        clean = deadline_text.strip()

        # ISO format: YYYY-MM-DD
        iso_match = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", clean)
        if iso_match:
            try:
                return date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
            except ValueError:
                pass

        # Month Day, Year (e.g., 'December 15, 2025')
        mdy_match = re.search(
            r"\b([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b",
            clean
        )
        if mdy_match:
            m_str, d_str, y_str = mdy_match.group(1).lower(), mdy_match.group(2), mdy_match.group(3)
            if m_str in cls.MONTHS:
                try:
                    return date(int(y_str), cls.MONTHS[m_str], int(d_str))
                except ValueError:
                    pass

        # Day Month Year (e.g., '15 October 2025' or '15th October 2025')
        dmy_match = re.search(
            r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+),?\s+(\d{4})\b",
            clean
        )
        if dmy_match:
            d_str, m_str, y_str = dmy_match.group(1), dmy_match.group(2).lower(), dmy_match.group(3)
            if m_str in cls.MONTHS:
                try:
                    return date(int(y_str), cls.MONTHS[m_str], int(d_str))
                except ValueError:
                    pass

        # Year and Month only (e.g., 'December 2025') -> assume end of month
        ym_match = re.search(r"\b([A-Za-z]+)\s+(\d{4})\b", clean)
        if ym_match:
            m_str, y_str = ym_match.group(1).lower(), ym_match.group(2)
            if m_str in cls.MONTHS:
                month_num = cls.MONTHS[m_str]
                year_num = int(y_str)
                # Pick 28th as safe approximation
                return date(year_num, month_num, 28)

        return None

    @classmethod
    def evaluate_status(
        cls,
        deadline_text: str,
        open_date_text: Optional[str] = None,
        is_rolling: bool = False,
        is_extended: bool = False,
        reference_date: Optional[date] = None,
    ) -> Tuple[DeadlineStatusType, Optional[date], str]:
        """
        Deterministically evaluates deadline status against the reference date.
        Returns: (status, parsed_date, explanation)
        """
        curr = cls.get_current_date(reference_date)
        text_lower = (deadline_text or "").lower()

        if is_rolling or "rolling" in text_lower:
            return "rolling_admissions", None, "Program operates on rolling admissions policy."

        if is_extended:
            return "extended_pending_verification", None, "Deadline extension reported; pending official confirmation."

        parsed_deadline = cls.parse_deadline_text(deadline_text)
        if not parsed_deadline:
            if "closed" in text_lower:
                return "closed", None, "Application cycle stated as closed."
            return "unknown", None, "Application deadline date could not be deterministically determined."

        # If deadline is in the past relative to current date
        if parsed_deadline < curr:
            return (
                "closed",
                parsed_deadline,
                f"Application deadline ({parsed_deadline.isoformat()}) has passed relative to current date ({curr.isoformat()})."
            )

        # If an open date is provided and current date is before open date
        if open_date_text:
            parsed_open = cls.parse_deadline_text(open_date_text)
            if parsed_open and curr < parsed_open:
                return (
                    "upcoming_not_open",
                    parsed_deadline,
                    f"Applications do not open until {parsed_open.isoformat()} (deadline: {parsed_deadline.isoformat()})."
                )

        # A future closing date only proves that a date was published; it does
        # not prove that the application window has opened.  Callers must pass
        # an evidenced opening date (or explicit ``applications_open`` flag)
        # before presenting a cycle as actionable.
        if not open_date_text:
            return (
                "upcoming_not_open",
                parsed_deadline,
                f"A future deadline ({parsed_deadline.isoformat()}) is published, but no official application-window opening evidence was retrieved."
            )

        return (
            "open",
            parsed_deadline,
            f"Applications currently open until deadline {parsed_deadline.isoformat()}."
        )
