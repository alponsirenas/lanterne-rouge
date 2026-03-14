# memory.py
# Simple JSONL-based history log — replaces the SQLite memory_bus.
#
# One JSON object per line, newest entries at the end of the file.
# Readable with any text editor; no database required.

import json
from datetime import datetime, timezone
from pathlib import Path

MEMORY_FILE = Path("memory/history.jsonl")


def append(entry_type: str, data: dict) -> None:
    """Append a timestamped entry to the history log."""
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": entry_type,
        "data": data,
    }
    with MEMORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def recent(n: int = 10) -> list[dict]:
    """Return the last `n` entries from the history log."""
    if not MEMORY_FILE.exists():
        return []
    lines = MEMORY_FILE.read_text(encoding="utf-8").strip().splitlines()
    entries = []
    for line in lines[-n:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries
