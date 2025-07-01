#!/usr/bin/env python3
"""
Comprehensive test for Lanterne Rouge reasoning modes.
Tests both default configuration and explicit mode selection.
"""

import os
from datetime import date
from dotenv import load_dotenv

# Add project to path
from setup import setup_path
setup_path()

# Load environment variables
load_dotenv()

# Import local modules
from src.lanterne_rouge.mission_config import bootstrap
from src.lanterne_rouge.tour_coach import TourCoach

def test_reasoning_modes():
    """Test all aspects of the reasoning system: default mode and explicit mode selection."""
    # Load mission config
    config = bootstrap("missions/tdf_sim_2025.toml")

    # Sample metrics
    metrics = {
        "readiness_score": 72,
        "ctl": 45,
        "atl": 52,
        "tsb": -7,
        "resting_heart_rate": 48,
        "hrv": 42
    }

    print("=" * 80)
    print("TESTING LANTERNE ROUGE REASONING MODES")
    print("=" * 80)

    # PART 1: Test Default Configuration
    print("\n🧪 TESTING DEFAULT REASONING MODE")
    print("-" * 50)

    # Default initialization (should be LLM if API key available)
    coach_default = TourCoach(config)  # No explicit use_llm_reasoning parameter
    print("Default TourCoach() initialization:")
    print(f"Reasoning Agent use_llm: {coach_default.reasoning_agent.use_llm}")

    # Check if API key exists
    api_key_exists = bool(os.getenv("OPENAI_API_KEY"))
    print(f"OpenAI API Key available: {api_key_exists}")

    # Generate decision to see which mode is actually used
    print("Generating decision with default settings...")
    decision = coach_default.reasoning_agent.make_decision(metrics, config, date.today())

    # Analyze the decision to determine if it's LLM or rule-based
    is_llm_decision = len(decision.reason) > 50  # LLM typically gives longer explanations
    print(f"Decision: {decision.action}")
    print(f"Reason length: {len(decision.reason)} chars")
    print(f"Likely LLM-based: {is_llm_decision}")

    if api_key_exists and is_llm_decision:
        print("✅ SUCCESS: LLM mode is default and working")
    elif api_key_exists and not is_llm_decision:
        print("⚠️  WARNING: API key exists but rule-based logic used")
    else:
        print("ℹ️  INFO: No API key, falling back to rule-based (expected)")

    # PART 2: Test Both Modes Explicitly
    print("\n\n🤖 RULE-BASED REASONING MODE (EXPLICIT)")
    print("-" * 50)

    coach_rule = TourCoach(config, use_llm_reasoning=False)
    summary_rule = coach_rule.generate_daily_recommendation(metrics)

    print(summary_rule)

    # Test LLM-based reasoning (if API key available)
    if os.getenv("OPENAI_API_KEY"):
        print("\n\n🧠 LLM-BASED REASONING MODE (EXPLICIT)")
        print("-" * 50)

        coach_llm = TourCoach(config, use_llm_reasoning=True, llm_model="gpt-4-turbo-preview")
        summary_llm = coach_llm.generate_daily_recommendation(metrics)

        print(summary_llm)

        print("\n" + "=" * 80)
        print("COMPARISON: Both modes produce structured, agent-based output")
        print("Rule-based: Fast, deterministic, offline")
        print("LLM-based: Contextual, adaptive, requires API key")
        print("=" * 80)
    else:
        print("\n\n❌ LLM-BASED REASONING SKIPPED")
        print("Set OPENAI_API_KEY environment variable to test LLM reasoning")
        print("=" * 80)

if __name__ == "__main__":
    test_reasoning_modes()
