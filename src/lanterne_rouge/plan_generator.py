import os
import json
import logging
import openai

from lanterne_rouge.mission_config import MissionConfig
from lanterne_rouge.monitor import get_oura_readiness, get_ctl_atl_tsb

logger = logging.getLogger(__name__)


def generate_workout_plan(mission_cfg: MissionConfig, memory: dict):
    """
    Use OpenAI to generate today's workout plan based on mission and current metrics.
    Returns a dict conforming to workout_plan.schema.json.
    """
    # Gather current metrics
    readiness, _ = get_oura_readiness()
    ctl, atl, tsb = get_ctl_atl_tsb()
    metrics = {"readiness": readiness, "ctl": ctl, "atl": atl, "tsb": tsb}

    # Build prompt
    prompt = (
        f"Mission configuration:\n{mission_cfg.model_dump_json()}\n"
        f"Recent memory entries:\n{json.dumps(memory)}\n"
        f"Current metrics:\n{json.dumps(metrics)}\n"
        "Generate a workout_plan JSON matching workout_plan.schema.json. Return only the JSON object."
    )

    # Call OpenAI with basic error handling
    try:
        resp = openai.ChatCompletion.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            messages=[
                {"role": "system", "content": "You are a workout planning assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        # Parse and return
        return json.loads(resp.choices[0].message.content)
    except openai.OpenAIError as e:  # pragma: no cover - depends on API
        logger.error(f"❌ OpenAI request failed: {e}")
        return {}
    except Exception as e:  # Fallback for unexpected issues
        logger.error(f"❌ OpenAI request failed: {e}")
        return {}
