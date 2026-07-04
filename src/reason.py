"""Score the stage against its target blocks and ask the coach for the verdicts.

The code computes facts (hit_target), the model writes the judgment. No rule trees.
"""

import json
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "coach.md"

ZONE_KEYS = ["z1", "z2", "z3", "z4", "z5"]
BLOCK_TOLERANCE = 0.75  # a block is held at 75% of its prescribed minutes


def hit_target(targets: list[dict], tiz: dict | None) -> bool | None:
    """Were the prescribed blocks held? Each target block asks for a minimum number
    of minutes at its zone or above. Returns None when there is no zone data,
    finished without context is not a miss."""
    if not tiz:
        return None
    for block in targets:
        floor = ZONE_KEYS.index(block["zone"])
        achieved = sum(tiz.get(z, 0) for z in ZONE_KEYS[floor:])
        if achieved < block["minutes"] * BLOCK_TOLERANCE:
            return False
    return True


def coach(payload: dict) -> dict:
    """One call: the coach reads the morning facts and returns the verdict JSON,
    {"yesterday": {"call", "note"} | null, "today": {"recommendation", "note"}}."""
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5"),
        max_tokens=1000,
        system=PROMPT_PATH.read_text(encoding="utf-8"),
        messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)}],
    )
    text = next((block.text for block in message.content if block.type == "text"), "")
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Coach did not return JSON: {text!r}")
    verdict = json.loads(text[start:end + 1])
    if "today" not in verdict:
        raise ValueError(f"Coach reply missing 'today': {verdict!r}")
    return verdict
