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
    memories_limit: int = 5
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

    raw_response = call_llm(messages)
    # Split the raw LLM response into individual recommendation lines.
    # The model might return a block of text with newlines or bullets.
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
    lines = [line.strip("- \t") for line in raw_response.splitlines()]
    return [line for line in lines if line]


def call_llm(
    messages: list[dict],
    model: str = "gpt-4", 
    temperature: float = 0.7, 
    max_tokens: int = 512
) -> str:
    """
    Send a chat completion request to the OpenAI API.

    Args:
        messages: A list of message dicts, each with 'role' ('system', 'user', 'assistant') and 'content'.
        model: The OpenAI model to use (default 'gpt-4').
        temperature: Sampling temperature (default 0.7).
        max_tokens: Maximum number of tokens in the response (default 512).

    Returns:
        The assistant's reply content.
    """
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
    if not isinstance(content, dict) or "workouts" not in content:
        raise ValueError("LLM response missing required 'workouts' key")
    return content
