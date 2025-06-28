"""
AI client interfaces for Lanterne Rouge.

This module provides utilities for interacting with AI models like OpenAI,
adapting responses for workout adjustments, and handling structured output.
"""
import json
import os

import openai

from lanterne_rouge.memory_bus import fetch_recent_memories

# Models that natively support the `response_format={"type": "json_object"}` parameter
_MODELS_WITH_JSON_SUPPORT = {
    "gpt-4o-preview",
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo-preview",
    "gpt-4-0125-preview",
    "gpt-4-1106-preview",
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-0125",
    "gpt-4o-2024-05-13",
}


def _model_supports_json(model: str) -> bool:
    """
    Return True if the specified model supports the structured JSON response
    format. This lets us add the `response_format` parameter only when it's
    accepted by the model to avoid HTTP 400 errors.
    """
    # Check if model is in our explicit list or has specific prefixes that indicate JSON support
    return (model in _MODELS_WITH_JSON_SUPPORT or
            model.endswith("-json") or
            model.startswith(("gpt-4-turbo", "gpt-4o")))


# Initialize OpenAI API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_workout_adjustment(
    readiness_score: float,
    readiness_details: dict,
    ctl: float,
    atl: float,
    tsb: float,
    mission_cfg,
    memories_limit: int = 5,
    *,
    model: str | None = None,
) -> list[str]:
    """
    Generate workout adjustment using LLM, seeded with recent memories.

    Args:
        readiness_score: numeric readiness score from Oura.
        readiness_details: dict of all readiness contributor values.
        ctl: current Chronic Training Load.
        atl: current Acute Training Load.
        tsb: current Training Stress Balance.
        mission_cfg: your MissionConfig instance (to extract plan targets).
        memories_limit: how many past memories to include.
        model: Optional model name to pass to the LLM. If omitted, the
            default from ``call_llm`` will be used.

    Returns:
        List of GPT-written adjustment recommendation lines.
        Each line has leading hyphens and whitespace stripped.
    """
    # Build a structured 'plan' dict out of your mission config
    try:
        current_plan = mission_cfg.dict()
    except (AttributeError, TypeError) as e:
        print(f"Warning: Could not convert mission config to dict: {e}")
        current_plan = {}

    # Aggregate all metrics together
    combined_metrics = {
        "readiness_score": readiness_score,
        **readiness_details,
        "ctl": ctl,
        "atl": atl,
        "tsb": tsb,
    }

    # Pull in recent memories to provide richer context
    recent_memories = fetch_recent_memories(limit=memories_limit)

    # Kick things off with a clear system prompt
    messages = [
        {
            "role": "system",
            "content": (
                "You are a smart cycling coach AI. Based on the mission targets, today's plan, "
                "and recent performance/readiness, propose any adjustments."
            ),
        }
    ]
    if recent_memories:
        mem_lines = [json.dumps(m) for m in recent_memories]
        messages.append(
            {
                "role": "system",
                "content": "Recent observations & decisions:\n" + "\n".join(mem_lines),
            }
        )

    # Now give the AI the current plan and fresh metrics
    user_content = (
        f"Mission plan:\n{current_plan}\n\n"
        f"Today's metrics:\n{combined_metrics}\n\n"
        "Please suggest workout modifications or validate the plan."
    )
    messages.append({"role": "user", "content": user_content})

    try:
        # Always call with force_json=False to avoid API compatibility issues
        raw_response = call_llm(messages, model=model, force_json=False)

        # Try to parse the response - first check if it's a bullet list
        if raw_response.lstrip().startswith("-"):
            lines = parse_llm_list(raw_response)
            return lines

        # Then try to parse as JSON if it looks like JSON
        if raw_response.strip().startswith("{") and raw_response.strip().endswith("}"):
            try:
                parsed = json.loads(raw_response)
                if isinstance(parsed, list):
                    lines = [str(line).strip("- \t") for line in parsed if str(line).strip()]
                    return lines
                if isinstance(parsed, dict) and "recommendations" in parsed:
                    if isinstance(parsed["recommendations"], list):
                        lines = [str(line).strip("- \t")
                                 for line in parsed["recommendations"] if str(line).strip()]
                        return lines
            except json.JSONDecodeError:
                pass  # Failed to parse as JSON, continue to fallback

        # Try generic parsing of any free-text response
        lines = parse_llm_list(raw_response)
        if lines:
            return lines

        # If all else fails, provide a generic recommendation
        return ["Plan looks good. Continue with scheduled workout."]

    except Exception as e:
        print(f"Error generating workout adjustment: {e}")
        return ["Unable to generate recommendations. Proceed with scheduled workout."]


def parse_llm_list(raw_response: str) -> list[str]:
    """
    Parse the raw LLM response into a list of cleaned recommendation lines.

    Args:
        raw_response: The raw text response from the LLM.

    Returns:
        A list of non-empty, cleaned lines with bullets and extra whitespace removed.
    """
    lines = [
        line.lstrip("-0123456789. \t").strip()
        for line in raw_response.splitlines()
    ]
    return [line for line in lines if line]


def call_llm(
    messages: list[dict],
    model: str | None = None,
    *,
    temperature: float = 0.7,
    max_tokens: int = 512,
    force_json: bool = False,  # Changed default to False for better compatibility
) -> str:
    """
    Send a chat completion request to the OpenAI API.

    Args:
        messages: A list of message dicts, each with 'role' ('system', 'user', 'assistant') and 'content'.
        model: The OpenAI model to use. Defaults to the value of the
            ``OPENAI_MODEL`` environment variable or ``"gpt-3.5-turbo"`` if unset.
        temperature: Sampling temperature (default 0.7).
        max_tokens: Maximum number of tokens in the response (default 512).
        force_json: If True, will request a structured JSON response
            from models that support it. If False (default), lets the model reply in freeform text.

    Returns:
        The assistant's reply content.
    """
    # Resolve model
    if model is None:
        # Default to a model that can handle JSON
        model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    # Set up request parameters
    response_kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # Only add response_format for models that explicitly support it
    if force_json and _model_supports_json(model):
        response_kwargs["response_format"] = {"type": "json_object"}

    try:
        # Use the new OpenAI client API
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(**response_kwargs)

        # Get the content from the response
        content = response.choices[0].message.content

        # Handle empty responses
        if content is None or content.strip() == "":
            return "- No valid response received from the model."

        return content

    except Exception as e:
        print(f"❌ OpenAI request failed: {e}")
        return "- Error: Could not get a response from the LLM."
