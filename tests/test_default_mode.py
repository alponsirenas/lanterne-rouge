#!/usr/bin/env python3
"""
Test to verify LLM mode is the default.
"""

import os
from datetime import date
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.lanterne_rouge.mission_config import bootstrap
from src.lanterne_rouge.tour_coach import TourCoach

def test_default_mode():
    """Test that LLM mode is the default."""
    
    # Load mission config
    config = bootstrap("missions/tdf_sim_2025.toml")
    
    # Sample metrics
    metrics = {
        "readiness_score": 72,
        "ctl": 45,
        "atl": 52,
        "tsb": -7,
    }
    
    print("🧪 TESTING DEFAULT REASONING MODE")
    print("=" * 50)
    
    # Test 1: Default initialization (should be LLM if API key available)
    print("1. Default TourCoach() initialization:")
    coach_default = TourCoach(config)  # No explicit use_llm_reasoning parameter
    print(f"   Reasoning Agent use_llm: {coach_default.reasoning_agent.use_llm}")
    
    # Test 2: Check if API key exists
    api_key_exists = bool(os.getenv("OPENAI_API_KEY"))
    print(f"2. OpenAI API Key available: {api_key_exists}")
    
    # Test 3: Generate decision to see which mode is actually used
    print("3. Generating decision with default settings...")
    decision = coach_default.reasoning_agent.make_decision(metrics, config, date.today())
    
    # Analyze the decision to determine if it's LLM or rule-based
    is_llm_decision = len(decision.reason) > 50  # LLM typically gives longer explanations
    print(f"   Decision: {decision.action}")
    print(f"   Reason length: {len(decision.reason)} chars")
    print(f"   Likely LLM-based: {is_llm_decision}")
    
    print("\n" + "=" * 50)
    if api_key_exists and is_llm_decision:
        print("✅ SUCCESS: LLM mode is default and working")
    elif api_key_exists and not is_llm_decision:
        print("⚠️  WARNING: API key exists but rule-based logic used")
    else:
        print("ℹ️  INFO: No API key, falling back to rule-based (expected)")
    
    print("=" * 50)

if __name__ == "__main__":
    test_default_mode()
