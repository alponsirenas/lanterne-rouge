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
    # Look for prompts directory relative to project root
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent.parent  # Navigate to project root
    prompt_path = project_root / "prompts" / "mission_builder.md"
    
    if not prompt_path.exists():
        logger.warning(f"Prompt template not found at {prompt_path}, using fallback")
        return _get_fallback_prompt()
    
    with open(prompt_path, 'r') as f:
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


def _build_questionnaire_prompt(questionnaire: MissionBuilderQuestionnaire) -> str:
    """Build the user prompt from questionnaire data."""
    preferred_days = questionnaire.preferred_training_days or ["Not specified"]
    if isinstance(preferred_days, list):
        days_str = ", ".join(preferred_days)
    else:
        days_str = str(preferred_days)
    
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
- Morning Briefing: {questionnaire.notification_preferences.morning_briefing}
- Evening Summary: {questionnaire.notification_preferences.evening_summary}
- Weekly Review: {questionnaire.notification_preferences.weekly_review}

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
    
    client = openai.OpenAI(api_key=api_key)
    
    # Load prompt template
    system_prompt = _load_prompt_template()
    user_prompt = _build_questionnaire_prompt(questionnaire)
    
    # Log redacted version
    redacted_data = _redact_sensitive_data(questionnaire.model_dump())
    logger.info(f"Generating mission draft for questionnaire: {redacted_data}")
    
    # Prepare messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
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
            f"First attempt produced malformed JSON: {error}. "
            "Retrying with temperature=0"
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
    
    if error:
        logger.error(f"Failed to generate mission draft after retry: {error}")
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


async def _call_llm_with_retry(
    client: openai.OpenAI,
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
        response = client.chat.completions.create(**api_params)
        
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
                json_str = content[start:end].strip()
                draft_data = json.loads(json_str)
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                json_str = content[start:end].strip()
                draft_data = json.loads(json_str)
            else:
                raise json.JSONDecodeError("No valid JSON found", content, 0)
        
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
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)
        
        logger.info(f"Logged mission draft to {log_file}")
        
    except Exception as e:
        logger.warning(f"Failed to log to file: {e}")
