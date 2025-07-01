#!/usr/bin/env python3
"""
Test script to demonstrate both rule-based and LLM-based reasoning modes.
"""

import os
from datetime import date
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.lanterne_rouge.mission_config import bootstrap
from src.lanterne_rouge.tour_coach import TourCoach

def test_reasoning_modes():
    """Test both rule-based and LLM-based reasoning modes."""
    
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
    
    # Test 1: Rule-based reasoning
    print("\n🤖 RULE-BASED REASONING MODE")
    print("-" * 40)
    
    coach_rule = TourCoach(config, use_llm_reasoning=False)
    summary_rule = coach_rule.generate_daily_recommendation(metrics)
    
    print(summary_rule)
    
    # Test 2: LLM-based reasoning (if API key available)
    if os.getenv("OPENAI_API_KEY"):
        print("\n\n🧠 LLM-BASED REASONING MODE")
        print("-" * 40)
        
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
