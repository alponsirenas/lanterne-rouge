# Mission Builder Prompts

This directory contains prompt templates for the LLM-powered mission builder feature.

## Overview

The mission builder uses OpenAI's GPT-4o-mini model in JSON mode to generate personalized training mission configurations based on user questionnaire responses.

## Files

- **`mission_builder.md`**: Main prompt template for generating mission drafts
  - Comprehensive guidelines for mission planning
  - Mission type-specific recommendations
  - Periodization strategies
  - Points schema design principles

## Usage

The prompt template is automatically loaded by the `mission_builder` service when generating mission drafts via the `POST /missions/draft` API endpoint.

### API Usage Example

```python
import requests

# Authenticate
auth_response = requests.post("http://localhost:8000/auth/login", json={
    "email": "user@example.com",
    "password": "password"
})
token = auth_response.json()["access_token"]

# Create mission draft
headers = {"Authorization": f"Bearer {token}"}
questionnaire = {
    "event_name": "Unbound 200",
    "event_date": "2025-06-07",
    "mission_type": "gravel_ultra",
    "weekly_hours": {"min": 8, "max": 12},
    "current_ftp": 250,
    "preferred_training_days": ["Monday", "Wednesday", "Saturday"],
    "constraints": "No injuries. Weekend mornings work best.",
    "riding_style": "steady",
    "notification_preferences": {
        "morning_briefing": True,
        "evening_summary": True,
        "weekly_review": True
    }
}

response = requests.post(
    "http://localhost:8000/missions/draft",
    json=questionnaire,
    headers=headers
)

draft = response.json()["draft"]
print(f"Generated mission: {draft['name']}")
print(f"Prep starts: {draft['prep_start']}")
print(f"Event date: {draft['event_start']}")
```

## Prompt Engineering Notes

### Design Principles

1. **Clear Structure**: The prompt provides explicit JSON schema requirements
2. **Context-Rich**: Includes mission type-specific guidance and examples
3. **Realistic Expectations**: Guidelines ensure achievable plans based on constraints
4. **Safety-First**: Emphasizes appropriate periodization and recovery

### Supported Mission Types

- `gravel_ultra`: 100+ mile gravel events (focus on endurance)
- `road_century`: 100km-100mi road rides (mixed endurance/tempo)
- `crit_series`: Criterium racing (high-intensity intervals)
- `gran_fondo`: Climbing-focused events (threshold work)
- `time_trial`: Individual time trials (sustained power)
- `stage_race`: Multi-day events (consistency)
- `endurance`: General endurance goals
- `general_fitness`: Broad fitness improvement

### Retry Logic

The system implements a two-attempt strategy:

1. **First Attempt**: Standard call with temperature=0.7 for creativity
2. **Second Attempt**: If JSON is malformed, retry with:
   - `temperature=0` for deterministic output
   - Clarification message requesting valid JSON only

### Privacy & Logging

All LLM interactions are logged to `logs/mission_builder/` with:
- Sensitive data redacted (FTP, specific constraints, training days)
- Event names partially redacted (first and last word only)
- Timestamps and token usage tracked

Logs are excluded from version control via `.gitignore`.

## Customization

To modify the prompt template:

1. Edit `mission_builder.md` with your changes
2. Test with the API endpoint
3. Review generated missions for quality
4. Adjust guidelines as needed

**Note**: Changes to the prompt may affect mission generation consistency. Test thoroughly before deploying to production.

## Model Configuration

- **Default Model**: `gpt-4o-mini`
- **JSON Mode**: Enabled (ensures structured output)
- **Temperature**: 0.7 (first attempt), 0 (retry)
- **Max Tokens**: 2000 (sufficient for detailed coaching notes)

## Error Handling

The service handles several error scenarios:

- **Malformed JSON**: Automatic retry with clarification
- **Missing API Key**: 502 error with descriptive message
- **API Failures**: 502 error with generic message (exception details are logged server-side for debugging)
- **Validation Errors**: 400/422 with field-specific feedback

## Testing

Comprehensive tests are available in `tests/test_mission_builder.py`:

- Schema validation tests
- Mock LLM integration tests
- Error handling tests
- Retry logic tests

Run tests with:
```bash
pytest tests/test_mission_builder.py -v
```
