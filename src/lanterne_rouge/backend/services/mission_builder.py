"""Mission builder service using LLM to generate personalized mission configurations."""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

import openai
from pydantic import ValidationError

from lanterne_rouge.backend.schemas.mission_builder import (
    MissionBuilderQuestionnaire,
    MissionDraft,
    MissionDraftResponse,
    NotificationPreferences,
)

logger = logging.getLogger(__name__)

# Models that support JSON mode
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
    """Check if model supports JSON mode."""
    return (model in _MODELS_WITH_JSON_SUPPORT or
            model.endswith("-json") or
            model.startswith(("gpt-4-turbo", "gpt-4o")))


def _load_prompt_template() -> str:
    """Load the mission builder prompt template."""
    # Robustly find project root by searching for "prompts" directory
    current_file = Path(__file__)
    project_root = current_file.parent
    found_prompts_dir = False
    while project_root != project_root.parent:
        if (project_root / "prompts").exists():
            found_prompts_dir = True
            break
        project_root = project_root.parent

    if not found_prompts_dir:
        logger.error(
            "Could not find 'prompts' directory in any parent of %s. Using fallback prompt.",
            current_file
        )
        return _get_fallback_prompt()

    prompt_path = project_root / "prompts" / "mission_builder.md"

    if not prompt_path.exists():
        logger.warning("Prompt template not found at %s, using fallback", prompt_path)
        return _get_fallback_prompt()

    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def _get_fallback_prompt() -> str:
    """Fallback prompt template if file not found."""
    return """You are an expert cycling coach AI. Generate a personalized \
mission configuration based on the questionnaire.

Return valid JSON with this structure:
{
  "name": "Mission name",
  "mission_type": "type from questionnaire",
  "prep_start": "YYYY-MM-DD",
  "event_start": "YYYY-MM-DD",
  "event_end": "YYYY-MM-DD",
  "points_schema": {
    "description": "Points system explanation",
    "daily_base": 15,
    "intensity_multipliers": {
      "easy": 1.1,
      "moderate": 1.8,
      "hard": 2.8
    }
  },
  "constraints": {
    "min_readiness": 70,
    "min_tsb": -12,
    "max_weekly_hours": 12
  },
  "notification_preferences": {
    "channel": "app",
    "morning_briefing": true,
    "evening_summary": true,
    "weekly_review": true
  },
  "notes": "Detailed coaching notes about periodization, weekly structure, \
key workouts, event strategy, and recovery."
}

Be realistic about timeframes and respect the athlete's constraints."""


def _redact_sensitive_data(data: dict) -> dict:
    """Redact sensitive information from logs."""
    redacted = data.copy()
    # Fields to redact or partially redact
    sensitive_fields = ['current_ftp', 'constraints', 'preferred_training_days']

    for field in sensitive_fields:
        if field in redacted:
            redacted[field] = "[REDACTED]"

    # Partially redact event name (keep first/last word)
    if 'event_name' in redacted:
        event_name = redacted['event_name']
        words = event_name.split()
        if len(words) > 2:
            redacted['event_name'] = f"{words[0]} ... {words[-1]}"

    return redacted


def _format_notification_preferences(prefs: Optional[NotificationPreferences]) -> str:
    """Format notification preferences for prompt."""
    if prefs is None:
        return "Not specified"
    return (
        f"- Channel: {prefs.channel}\n"
        f"- Morning Briefing: {prefs.morning_briefing}\n"
        f"- Evening Summary: {prefs.evening_summary}\n"
        f"- Weekly Review: {prefs.weekly_review}"
    )


def _build_questionnaire_prompt(questionnaire: MissionBuilderQuestionnaire) -> str:
    """Build the user prompt from questionnaire data."""
    preferred_days = questionnaire.preferred_training_days or ["Not specified"]
    days_str = ", ".join(preferred_days)

    constraints_str = questionnaire.constraints or "None specified"

    prompt = f"""Generate a mission configuration for this athlete:

Event Information:
- Event Name: {questionnaire.event_name}
- Event Date: {questionnaire.event_date.isoformat()}
- Mission Type: {questionnaire.mission_type}

Athlete Profile:
- Current FTP: {questionnaire.current_ftp}W
- Weekly Training Hours: {questionnaire.weekly_hours.min}-{questionnaire.weekly_hours.max} hours
- Preferred Training Days: {days_str}
- Riding Style Preference: {questionnaire.riding_style}

Constraints:
{constraints_str}

Notification Preferences:
{_format_notification_preferences(questionnaire.notification_preferences)}

Please generate a complete, realistic mission configuration in JSON format."""

    return prompt


async def generate_mission_draft(
    questionnaire: MissionBuilderQuestionnaire,
    model: str = "gpt-4o-mini",
    log_to_file: bool = True
) -> Tuple[Optional[MissionDraftResponse], Optional[str]]:
    """
    Generate a mission draft using LLM based on questionnaire input.
    
    Args:
        questionnaire: User's questionnaire responses
        model: OpenAI model to use (default: gpt-4o-mini)
        log_to_file: Whether to log prompts/responses to file
    
    Returns:
        Tuple of (MissionDraftResponse or None, error_message or None)
    """
    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        error_msg = "OPENAI_API_KEY environment variable not set"
        logger.error(error_msg)
        return None, error_msg
    
    client = openai.AsyncOpenAI(api_key=api_key)
    
    # Load prompt template and build messages
    system_prompt = _load_prompt_template()
    user_prompt = _build_questionnaire_prompt(questionnaire)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Log redacted version
    redacted_data = _redact_sensitive_data(questionnaire.model_dump())
    logger.info("Generating mission draft for questionnaire: %s", redacted_data)
    
    # Try generating the draft
    response_data, error = await _generate_with_retry(client, model, messages)
    
    if error:
        logger.error("Failed to generate mission draft after retry: %s", error)
        return None, error

    # Parse and validate response
    try:
        draft = MissionDraft(**response_data['draft'])
        
        # Create response
        response = MissionDraftResponse(
            draft=draft,
            generated_at=datetime.now(timezone.utc).isoformat(),
            model_used=model,
            prompt_tokens=response_data.get('prompt_tokens'),
            completion_tokens=response_data.get('completion_tokens')
        )
        
        # Optional file logging
        if log_to_file:
            _log_to_file(questionnaire, response, redacted=True)
        
        logger.info("Successfully generated mission draft")
        return response, None
        
    except ValidationError as e:
        error_msg = f"Generated draft failed validation: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


async def _generate_with_retry(
    client: openai.AsyncOpenAI,
    model: str,
    messages: list
) -> Tuple[Optional[dict], Optional[str]]:
    """Generate draft with retry logic for malformed JSON."""
    # First attempt with default temperature
    response_data, error = await _call_llm_with_retry(
        client=client,
        model=model,
        messages=messages,
        temperature=0.7,
        attempt=1
    )
    
    if error and "json" in error.lower():
        # Malformed JSON - retry with temperature=0 and clarification
        logger.warning(
            "First attempt produced malformed JSON: %s. Retrying with temperature=0",
            error
        )
        
        clarification_message = {
            "role": "user",
            "content": (
                "The previous response was not valid JSON. "
                "Please respond ONLY with valid JSON, no markdown formatting "
                "or extra text. Start directly with { and end with }."
            )
        }
        messages.append(clarification_message)
        
        response_data, error = await _call_llm_with_retry(
            client=client,
            model=model,
            messages=messages,
            temperature=0,
            attempt=2
        )
    
    return response_data, error
async def _call_llm_with_retry(
    client: openai.AsyncOpenAI,
    model: str,
    messages: list,
    temperature: float,
    attempt: int
) -> Tuple[Optional[dict], Optional[str]]:
    """
    Call LLM and parse JSON response.

    Returns:
        Tuple of (response_dict or None, error_message or None)
    """
    try:
        # Prepare API call parameters
        api_params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2000,
        }

        # Add JSON mode if supported
        if _model_supports_json(model):
            api_params["response_format"] = {"type": "json_object"}

        # Make API call
        response = await client.chat.completions.create(**api_params)

        # Extract content
        content = response.choices[0].message.content

        # Parse JSON
        try:
            # Try direct parse
            draft_data = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end == -1:
                    raise json.JSONDecodeError("Malformed markdown code block", content, 0) from None
                json_str = content[start:end].strip()
                draft_data = json.loads(json_str)
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end == -1:
                    raise json.JSONDecodeError("Malformed markdown code block", content, 0) from None
                json_str = content[start:end].strip()
                draft_data = json.loads(json_str)
            else:
                raise json.JSONDecodeError("No valid JSON found", content, 0) from None

        # Prepare response data
        result = {
            'draft': draft_data,
            'prompt_tokens': response.usage.prompt_tokens if response.usage else None,
            'completion_tokens': response.usage.completion_tokens if response.usage else None,
        }

        return result, None

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse JSON from LLM response (attempt {attempt}): {str(e)}"
        logger.warning(error_msg)
        return None, error_msg

    except Exception as e:
        error_msg = f"LLM API call failed (attempt {attempt}): {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def _log_to_file(
    questionnaire: MissionBuilderQuestionnaire,
    response: MissionDraftResponse,
    redacted: bool = True
) -> None:
    """Log prompt and response to file for debugging/auditing."""
    try:
        # Create logs directory if needed
        log_dir = Path("logs/mission_builder")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Generate log filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"draft_{timestamp}.json"

        # Prepare log data
        log_data = {
            "timestamp": response.generated_at,
            "model": response.model_used,
            "questionnaire": (_redact_sensitive_data(questionnaire.model_dump())
                            if redacted else questionnaire.model_dump()),
            "draft": response.draft.model_dump(),
            "tokens": {
                "prompt": response.prompt_tokens,
                "completion": response.completion_tokens
            }
        }

        # Write to file
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, default=str)

        logger.info("Logged mission draft to %s", log_file)

    except (OSError, IOError) as e:
        logger.warning("Failed to log to file: %s", e)
