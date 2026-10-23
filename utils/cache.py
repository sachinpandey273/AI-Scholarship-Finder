"""
Local caching mechanism using SQLite for persisting research records,
raw webpage extracts, and queries with timestamps to prevent duplicate requests.
"""
from __future__ import annotations

import sqlite3
import json
from typing import Optional, Dict, Any
from datetime import datetime
from config import AppConfig

DB_PATH = AppConfig.CACHE_DIR / "research_cache.sqlite3"

def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cache_store (
            cache_key TEXT PRIMARY KEY,
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            source_url TEXT
        )
        """
    )
    return conn

def get_cached_item(cache_key: str) -> Optional[Dict[str, Any]]:
    """Retrieve an item from the cache if it exists."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data_json, created_at, source_url FROM cache_store WHERE cache_key = ?", (cache_key,))
            row = cursor.fetchone()
            if row:
                data = json.loads(row[0])
                if isinstance(data, dict):
                    data["_cached_at"] = row[1]
                    data["_cached_source_url"] = row[2]
                return data
    except Exception:
        return None
    return None

def set_cached_item(cache_key: str, data: Any, source_url: Optional[str] = None) -> None:
    """Store an item into SQLite cache with current timestamp."""
    try:
        with _get_connection() as conn:
            now_iso = datetime.utcnow().isoformat()
            conn.execute(
                """
                INSERT OR REPLACE INTO cache_store (cache_key, data_json, created_at, source_url)
                VALUES (?, ?, ?, ?)
                """,
                (cache_key, json.dumps(data), now_iso, source_url or "")
            )
    except Exception:
        pass

def clear_cache() -> None:
    """Clear all cached records."""
    try:
        with _get_connection() as conn:
            conn.execute("DELETE FROM cache_store")
    except Exception:
        pass
