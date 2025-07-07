"""
Input validation utilities for Lanterne Rouge system.

Provides security-focused validation for user inputs, API responses,
and configuration data to prevent injection attacks and data corruption.
"""

import json
import re
from typing import Dict, Any, List


def validate_llm_json_response(response: str, required_fields: List[str] = None) -> Dict[str, Any]:
    """Safely validate and parse LLM JSON responses.

    Args:
        response: Raw LLM response string
        required_fields: List of required field names

    Returns:
        Validated dictionary with sanitized values

    Raises:
        ValueError: If response is invalid or malicious
    """
    if not response or len(response) > 10000:  # Prevent massive responses
        raise ValueError("Invalid response length")

    try:
        data = json.loads(response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Response must be a JSON object")

    # Validate required fields
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

    # Sanitize string values to prevent injection
    sanitized_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized_data[key] = sanitize_string_input(value)
        elif isinstance(value, (int, float, bool)):
            sanitized_data[key] = value
        elif isinstance(value, list):
            # Sanitize list of strings
            sanitized_data[key] = [
                sanitize_string_input(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            # Skip unknown types for security
            continue

    return sanitized_data


def sanitize_string_input(input_str: str, max_length: int = 1000) -> str:
    """Sanitize string inputs to prevent injection attacks.

    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not isinstance(input_str, str):
        return ""

    # Truncate to max length
    sanitized = input_str[:max_length]

    # Remove potential script injection patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'expression\s*\(',
    ]

    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)

    # Remove control characters except newlines and tabs
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)

    return sanitized.strip()


def validate_ride_mode(ride_mode: str) -> str:
    """Validate ride mode input.

    Args:
        ride_mode: Ride mode string

    Returns:
        Validated ride mode

    Raises:
        ValueError: If ride mode is invalid
    """
    valid_modes = {"gc", "breakaway", "rest"}

    if not isinstance(ride_mode, str):
        raise ValueError("Ride mode must be a string")

    mode = ride_mode.lower().strip()
    if mode not in valid_modes:
        raise ValueError(f"Invalid ride mode: {mode}. Must be one of {valid_modes}")

    return mode


def validate_confidence_score(confidence: Any) -> float:
    """Validate confidence score.

    Args:
        confidence: Confidence value

    Returns:
        Validated confidence score between 0.0 and 1.0
    """
    try:
        score = float(confidence)
    except (ValueError, TypeError):
        return 0.5  # Default confidence

    # Clamp to valid range
    return max(0.0, min(1.0, score))


def validate_activity_data(activity_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate activity data from Strava API.

    Args:
        activity_data: Raw activity data

    Returns:
        Validated activity data with safe defaults
    """
    validated = {}

    # Validate numeric fields
    numeric_fields = {
        'moving_time': 0,
        'distance': 0,
        'average_watts': None,
        'weighted_average_watts': None,
        'suffer_score': None,
        'intensity_factor': None,
        'average_heartrate': None,
        'max_heartrate': None,
        'total_elevation_gain': 0,
        'calories': None,
        'average_speed': None,
        'max_speed': None
    }

    for field, default in numeric_fields.items():
        value = activity_data.get(field, default)
        if value is not None:
            try:
                validated[field] = max(0, float(value))  # Ensure non-negative
            except (ValueError, TypeError):
                validated[field] = default
        else:
            validated[field] = default

    # Validate string fields
    string_fields = ['name', 'description', 'sport_type']
    for field in string_fields:
        value = activity_data.get(field, '')
        validated[field] = sanitize_string_input(value, max_length=500)

    # Add computed fields for analysis
    validated['duration_minutes'] = validated.get('moving_time', 0) / 60
    validated['distance_km'] = validated.get('distance', 0) / 1000

    return validated


def validate_stage_info(stage_info: Dict[str, Any]) -> Dict[str, Any]:
    """Validate stage information.

    Args:
        stage_info: Raw stage info

    Returns:
        Validated stage info
    """
    validated = {}

    # Validate stage number
    stage_number = stage_info.get('number', 1)
    try:
        validated['number'] = max(1, min(21, int(stage_number)))
    except (ValueError, TypeError):
        validated['number'] = 1

    # Validate stage type
    valid_types = {'flat', 'hilly', 'mountain', 'itt', 'mtn_itt'}
    stage_type = stage_info.get('type', 'flat')
    if isinstance(stage_type, str) and stage_type.lower() in valid_types:
        validated['type'] = stage_type.lower()
    else:
        validated['type'] = 'flat'

    # Validate date
    if 'date' in stage_info:
        validated['date'] = stage_info['date']

    return validated


def calculate_power_metrics(activity_data: Dict[str, Any], ftp: int) -> Dict[str, Any]:
    """Calculate power-based training metrics using athlete's FTP.

    Args:
        activity_data: Validated activity data
        ftp: Athlete's Functional Threshold Power in watts

    Returns:
        Dictionary with calculated power metrics
    """
    metrics = {
        'intensity_factor': 0.0,
        'tss': 0.0,
        'normalized_power': 0.0,
        'effort_level': 'recovery'
    }

    if not ftp or ftp <= 0:
        return metrics

    # Get power data
    normalized_power = activity_data.get('weighted_average_watts', 0) or 0
    duration_hours = activity_data.get('duration_minutes', 0) / 60

    if normalized_power > 0 and duration_hours > 0:
        # Calculate Intensity Factor (IF)
        intensity_factor = normalized_power / ftp
        metrics['intensity_factor'] = round(intensity_factor, 3)
        metrics['normalized_power'] = normalized_power

        # Calculate Training Stress Score (TSS)
        # TSS = (duration_hours × IF^2 × 100)
        tss = duration_hours * (intensity_factor ** 2) * 100
        metrics['tss'] = round(tss, 1)

        # Determine effort level based on IF
        if intensity_factor < 0.55:
            metrics['effort_level'] = 'recovery'
        elif intensity_factor < 0.75:
            metrics['effort_level'] = 'aerobic'
        elif intensity_factor < 0.85:
            metrics['effort_level'] = 'tempo'
        elif intensity_factor < 0.95:
            metrics['effort_level'] = 'threshold'
        elif intensity_factor < 1.05:
            metrics['effort_level'] = 'vo2max'
        else:
            metrics['effort_level'] = 'neuromuscular'

    return metrics
