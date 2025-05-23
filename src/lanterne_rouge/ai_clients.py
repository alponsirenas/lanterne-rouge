#
# Models that natively support the `response_format={"type": "json_object"}` parameter
_MODELS_WITH_JSON_SUPPORT = {
    "gpt-4o-preview",
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-0125",
    "gpt-4o-2024-05-13",
}

def _model_supports_json(model: str) -> bool:
    """
    Return True if the specified model supports the structured JSON response
    format. This lets us add the `response_format` parameter only when it’s
    accepted by the model to avoid HTTP 400 errors.
    """
    return model in _MODELS_WITH_JSON_SUPPORT or model.endswith("-json")
import os
import json
import openai
from lanterne_rouge.memory_bus import fetch_recent_memories

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
        List of GPT-written adjustment recommendation lines. Each line has leading hyphens and whitespace stripped.
    """
    # Build a structured 'plan' dict out of your mission config
    try:
        current_plan = mission_cfg.dict()
    except Exception:
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

    raw_response = call_llm(messages, model=model, force_json=True)

    # The LLM may return either a bullet list or a JSON array of strings.
    # Attempt JSON parsing first; fall back to bullet parsing if that fails.
    try:
        parsed = json.loads(raw_response)
        if isinstance(parsed, list):
            lines = [str(line).strip("- \t") for line in parsed if str(line).strip()]
            return lines
        raise ValueError("Invalid JSON response from LLM")
    except json.JSONDecodeError:
        # If the response doesn't look like a bullet list either, treat it as invalid
        if not raw_response.strip().startswith("-"):
            # Fallback: parse as bullet/text list anyway
            pass
    # Parse simple bullet/text list
    lines = parse_llm_list(raw_response)
    return lines


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
    force_json: bool = True,
) -> str:
    """
    Send a chat completion request to the OpenAI API.

    Args:
        messages: A list of message dicts, each with 'role' ('system', 'user', 'assistant') and 'content'.
        model: The OpenAI model to use. Defaults to the value of the
            ``OPENAI_MODEL`` environment variable or ``"gpt-4"`` if unset.
        temperature: Sampling temperature (default 0.7).
        max_tokens: Maximum number of tokens in the response (default 512).
        force_json: If True (default), will request a structured JSON response
            from models that support it. If False, lets the model reply in freeform text.

    Returns:
        The assistant's reply content.
    """

    # Resolve model:
    # 1) explicit argument
    # 2) environment variable `OPENAI_MODEL`
    # 3) sensible lightweight default that supports JSON
    if model is None:
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-1106")

    # Decide whether we can request structured JSON directly
    response_kwargs: dict[str, object] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if force_json and _model_supports_json(model):
        response_kwargs["response_format"] = {"type": "json_object"}

    response = openai.chat.completions.create(**response_kwargs)
    content = response.choices[0].message.content
    return content
