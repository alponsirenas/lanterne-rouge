# coach.py
# The coaching brain — one Claude call, no fallback logic needed.
#
# Modern Claude models return reliable structured output, so we don't need
# dual-mode reasoning, JSON repair, or a separate rule-based fallback.
# The system prompt defines the decision space; Claude does the reasoning.

import json
import os
from datetime import date

import anthropic
from dotenv import load_dotenv

from .mission import MissionConfig
from .memory import recent

load_dotenv()

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

_SYSTEM = """\
You are an expert cycling coach. Your athlete shares their daily biometric data \
and training load, and you respond with a personalized recommendation for the day.

Always reply with a single JSON object — no markdown, no prose outside the JSON:
{
  "action": "recover | ease | maintain | push",
  "intensity": "low | moderate | high",
  "reason": "2-3 sentences addressing the athlete directly (use 'you'/'your'). \
Explain the decision in plain language and connect it to their goal.",
  "workout": "Concrete workout description, e.g. '60 min zone 2 at 60-70% FTP'",
  "flags": ["optional list of concerns, e.g. 'low_readiness', 'high_fatigue'"]
}

Decision guidelines:
- readiness < 70 OR tsb < -15  → bias toward recover/ease
- readiness 70-79 AND tsb < 0  → ease or maintain
- readiness ≥ 80 AND tsb ≥ 0  → maintain or push
- readiness ≥ 85 AND tsb > 5   → push

Be encouraging. Keep the reason conversational — no jargon without explanation.\
"""


def recommend(
    readiness: int,
    hrv_balance: int | None,
    ctl: float,
    atl: float,
    tsb: float,
    mission: MissionConfig,
    today: date,
) -> dict:
    """Call Claude once and return a structured coaching recommendation."""
    phase = mission.training_phase(today)
    days_to_goal = (mission.goal_date - today).days
    next_phase = mission.next_phase_start(today)
    days_to_next = (next_phase - today).days if next_phase else None
    history = recent(7)

    user_msg = f"""\
Today: {today}

Athlete metrics:
  Readiness score : {readiness}/100
  HRV balance     : {hrv_balance if hrv_balance is not None else "n/a"}
  CTL (fitness)   : {ctl}
  ATL (fatigue)   : {atl}
  TSB (form)      : {tsb}

Mission: {mission.name}{f" — {mission.goal_description}" if mission.goal_description else ""}
  Training phase  : {phase}{f" ({days_to_next}d until next phase)" if days_to_next else ""}
  Days to goal    : {days_to_goal}
  FTP             : {mission.athlete.ftp} W
  Min readiness   : {mission.constraints.min_readiness}
  Min TSB         : {mission.constraints.min_tsb}

Recent history ({len(history)} entries):
{json.dumps(history, indent=2) if history else "  (none yet)"}

Give me today's recommendation.\
"""

    response = _client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = response.content[0].text.strip()

    # Strip accidental markdown fences
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "action": "maintain",
            "intensity": "moderate",
            "reason": "Could not parse today's coaching recommendation. Check logs.",
            "workout": "Easy 60 min zone 2 ride",
            "flags": ["parse_error"],
        }
