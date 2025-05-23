import os
import json
import openai
import logging

from lanterne_rouge.mission_config import MissionConfig
from lanterne_rouge.monitor import get_oura_readiness, get_ctl_atl_tsb

logger = logging.getLogger(__name__)


def generate_workout_plan(mission_cfg: MissionConfig, memory: dict):
    """
    Use OpenAI to generate today's workout plan based on mission and current metrics.
    Returns a dict conforming to workout_plan.schema.json.
    """
    print("Generating workout plan...")

    # Gather current metrics
    readiness, *_ = get_oura_readiness()
    ctl, atl, tsb = get_ctl_atl_tsb()
    metrics = {"readiness": readiness, "ctl": ctl, "atl": atl, "tsb": tsb}

    # Build prompt
    prompt = (
        f"Mission configuration:\n{mission_cfg.model_dump_json()}\n"
        f"Recent memory entries:\n{json.dumps(memory)}\n"
        f"Current metrics:\n{json.dumps(metrics)}\n"
        "Generate a workout_plan JSON matching workout_plan.schema.json. Return only the JSON object. "
        "You MUST reply with a JSON object that contains a 'today' object and an 'adjustments' array as required by the schema. "
        "The schema requires: today.type, today.duration_minutes, today.intensity and adjustments array. "
        "The response must exactly match workout_plan.schema.json. No markdown or extra text."
    )

    # Call OpenAI with basic error handling
    try:
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Define response kwargs with a model that properly supports JSON generation
        model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        response_kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a workout planning assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
        }
        
        # Only add response_format for compatible models
        # Re-using the same logic as in ai_clients.py for model compatibility
        if (model.startswith(("gpt-4-turbo", "gpt-4o", "gpt-4-1106", "gpt-4-0125")) or
            model in ("gpt-3.5-turbo-1106", "gpt-3.5-turbo-0125")) and not model.startswith("gpt-4-vision"):
            response_kwargs["response_format"] = {"type": "json_object"}
            
        resp = client.chat.completions.create(**response_kwargs)
        # Parse and return
        plan = json.loads(resp.choices[0].message.content)
        if "today" not in plan or "adjustments" not in plan:
            raise ValueError("LLM response missing required keys ('today' and 'adjustments')")
        print("Workout plan generated successfully")
        return plan
    except (openai.OpenAIError, openai.APIError, openai.APIConnectionError) as e:  # pragma: no cover - depends on API
        logger.error(f"❌ OpenAI request failed: {e}")
        return {}
    except ValueError:
        raise
    except Exception as e:  # Fallback for unexpected issues
        logger.error(f"❌ OpenAI request failed: {e}")
        return {}
