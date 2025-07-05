"""
Memory module for Lanterne Rouge.

This module provides functionality for storing, retrieving, and managing
observations and memories for the AI reasoning system.
"""
import datetime
from pathlib import Path
import sqlite3
import json
from contextlib import contextmanager

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


@contextmanager
def _get_db_connection():
    """Context manager for database connections to ensure proper cleanup."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except Exception as e:
        # Rollback any pending transaction on error
        conn.rollback()
        raise e
    finally:
        # Always close the connection, even if an exception occurred
        conn.close()


def _get_conn():
    """Get a connection to the SQLite database with row factory set.

    Note: This is kept for backward compatibility but should be avoided.
    Use _get_db_connection() context manager instead.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def load_memory():
    """Load all memories from the database in chronological order."""
    with _get_db_connection() as conn:
        cursor = conn.execute("SELECT timestamp, type, data FROM memory ORDER BY timestamp")
        mem = {"observations": [], "decisions": [], "reflections": []}
        for row in cursor:
            try:
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
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Skipping corrupted memory entry: {e}")
                continue
    return mem


def log_observation(data):
    """Log an observation to the memory database.

    Args:
        data: The observation data to log (will be JSON serialized)
    """
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        with _get_db_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO memory (timestamp, type, data) VALUES (?, ?, ?)",
                (ts, "observation", json.dumps(data))
            )
            conn.commit()
    except (sqlite3.Error, json.JSONEncodeError) as e:
        print(f"Error logging observation: {e}")
        raise


def log_decision(data):
    """Log a decision to the memory database.

    Args:
        data: The decision data to log (will be JSON serialized)
    """
    # Fixed: Use UTC timezone consistently with other logging functions
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        with _get_db_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO memory (timestamp, type, data) VALUES (?, ?, ?)",
                (ts, "decision", json.dumps(data))
            )
            conn.commit()
    except (sqlite3.Error, json.JSONEncodeError) as e:
        print(f"Error logging decision: {e}")
        raise


def log_reflection(data):
    """Log a reflection to the memory database.

    Args:
        data: The reflection data to log (will be JSON serialized)
    """
    # Fixed: Use UTC timezone consistently with other logging functions
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        with _get_db_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO memory (timestamp, type, data) VALUES (?, ?, ?)",
                (ts, "reflection", json.dumps(data))
            )
            conn.commit()
    except (sqlite3.Error, json.JSONEncodeError) as e:
        print(f"Error logging reflection: {e}")
        raise


def fetch_recent_memories(limit: int):
    """
    Retrieve the most recent memory entries, across observations, decisions, and reflections,
    limited to the specified number of entries. Returns a list of dicts with keys:
    'timestamp', 'type', and 'data'.
    """
    try:
        with _get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT timestamp, type, data FROM memory ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()

            # parse JSON data and return entries, skipping corrupted ones
            result = []
            for row in rows:
                try:
                    result.append({
                        "timestamp": row["timestamp"],
                        "type": row["type"],
                        "data": json.loads(row["data"])
                    })
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Warning: Skipping corrupted memory entry: {e}")
                    continue
            return result
    except sqlite3.Error as e:
        print(f"Error fetching recent memories: {e}")
        return []
