"""
Memory Bus module for the Lanterne Rouge project.

This module provides functionality for storing and retrieving various types
of data (observations, decisions, and reflections) in a SQLite database,
which serves as the agent's memory system.
"""

import datetime
import json
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parents[2] / "memory" / "lanterne.db"
DB_FILE.parent.mkdir(parents=True, exist_ok=True)

_conn = sqlite3.connect(DB_FILE)
_conn.execute("""
CREATE TABLE IF NOT EXISTS memory (
    timestamp TEXT PRIMARY KEY,
    type TEXT,
    data TEXT
)
""")
_conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memory(type)")
_conn.commit()
_conn.close()


def _get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def load_memory():
    """
    Load all memory entries from the database.

    Returns:
        dict: Dictionary containing all observations, decisions, and reflections.
    """
    conn = _get_conn()
    cursor = conn.execute("SELECT timestamp, type, data FROM memory ORDER BY timestamp")
    mem = {"observations": [], "decisions": [], "reflections": []}
    for row in cursor:
        entry = {
            "timestamp": row["timestamp"],
            "data": json.loads(row["data"])
        }
        if row["type"] == "observation":
            mem["observations"].append(entry)
        elif row["type"] == "decision":
            mem["decisions"].append(entry)
        elif row["type"] == "reflection":
            mem["reflections"].append(entry)
    conn.close()
    return mem


def log_observation(data):
    """
    Log an observation to the memory database.

    Args:
        data: The observation data to log
    """
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = _get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO memory (timestamp, type, data) VALUES (?, ?, ?)",
        (ts, "observation", json.dumps(data))
    )
    conn.commit()
    conn.close()


def log_decision(data):
    """
    Log a decision to the memory database.

    Args:
        data: The decision data to log
    """
    ts = datetime.datetime.now().isoformat()
    conn = _get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO memory (timestamp, type, data) VALUES (?, ?, ?)",
        (ts, "decision", json.dumps(data))
    )
    conn.commit()
    conn.close()


def log_reflection(data):
    """
    Log a reflection to the memory database.

    Args:
        data: The reflection data to log
    """
    ts = datetime.datetime.now().isoformat()
    conn = _get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO memory (timestamp, type, data) VALUES (?, ?, ?)",
        (ts, "reflection", json.dumps(data))
    )
    conn.commit()
    conn.close()


def fetch_recent_memories(limit: int):
    """
    Retrieve the most recent memory entries, across observations, decisions, and reflections,
    limited to the specified number of entries. Returns a list of dicts with keys:
    'timestamp', 'type', and 'data'.
    """
    conn = _get_conn()
    cursor = conn.execute(
        "SELECT timestamp, type, data FROM memory ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    # parse JSON data and return entries
    return [
        {
            "timestamp": row["timestamp"],
            "type": row["type"],
            "data": json.loads(row["data"])
        }
        for row in rows
    ]
