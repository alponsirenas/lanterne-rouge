#!/usr/bin/env python3
"""
Lanterne Rouge Demo Script

This script demonstrates the key features of the Lanterne Rouge system,
showing both LLM-based and rule-based reasoning modes with sample data.
"""
import os
import sys
from datetime import date, timedelta
import argparse
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lanterne_rouge.mission_config import bootstrap
from src.lanterne_rouge.tour_coach import TourCoach


def demo_with_scenario(use_llm=True, llm_model=None, metrics=None, days_from_event=None):
    """
    Run a demo with specific scenario parameters.
    
    Args:
        use_llm (bool): Whether to use LLM-based reasoning
        llm_model (str, optional): The LLM model to use, if any
        metrics (dict, optional): Custom metrics to use
        days_from_event (int, optional): Days before the goal event
    """
    # Load mission config
    config = bootstrap("missions/tdf_sim_2025.toml")
    
    # Define a demo date based on days from the goal event
    demo_date = None
    if days_from_event is not None:
        demo_date = config.goal_date - timedelta(days=days_from_event)
    else:
        # Default to 30 days before the event
        demo_date = config.goal_date - timedelta(days=30)
    
    # Use provided metrics or set defaults
    if metrics is None:
        metrics = {
            "readiness_score": 75,
            "ctl": 55,
            "atl": 50,
            "tsb": 5,
            "resting_heart_rate": 48,
            "hrv": 65
        }
    
    # Create TourCoach with specified configuration
    coach = TourCoach(config, use_llm_reasoning=use_llm, llm_model=llm_model)
    
    # Display scenario information
    print("\n" + "=" * 80)
    print(f"📅 SCENARIO DATE: {demo_date} ({(config.goal_date - demo_date).days} days to goal)")
    print(f"🧠 REASONING MODE: {'LLM' if use_llm else 'Rule-based'}")
    if llm_model and use_llm:
        print(f"🤖 USING MODEL: {llm_model}")
    print(f"📊 METRICS: Readiness={metrics['readiness_score']}, CTL={metrics['ctl']}, " 
          f"ATL={metrics['atl']}, TSB={metrics['tsb']}")
    print("=" * 80)
    
    # Generate recommendation
    recommendation = coach.generate_daily_recommendation(
        metrics, 
        current_date=demo_date
    )
    
    # Display the result
    print(recommendation)
    print("\n")


def main():
    """Run the demo with command-line options."""
    parser = argparse.ArgumentParser(description="Lanterne Rouge Demo")
    parser.add_argument("--no-llm", action="store_true", help="Use rule-based reasoning only")
    parser.add_argument("--model", type=str, default="gpt-4-turbo-preview", 
                       help="LLM model to use (default: gpt-4-turbo-preview)")
    parser.add_argument("--days-to-goal", type=int, 
                       help="Days until the goal event (default: varies by scenario)")
    parser.add_argument("--readiness", type=int, default=75, 
                       help="Readiness score (0-100, default: 75)")
    parser.add_argument("--ctl", type=int, default=55, 
                       help="Chronic Training Load (default: 55)")
    parser.add_argument("--atl", type=int, default=50, 
                       help="Acute Training Load (default: 50)")
    parser.add_argument("--tsb", type=int, default=5, 
                       help="Training Stress Balance (default: 5)")
    parser.add_argument("--compare", action="store_true", 
                       help="Run both LLM and rule-based modes for comparison")
    args = parser.parse_args()
    
    # Check for OPENAI_API_KEY if using LLM
    if not args.no_llm and not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found. Set this environment variable for LLM mode.")
        print("   Proceeding with rule-based reasoning instead.")
        args.no_llm = True
    
    # Prepare metrics
    metrics = {
        "readiness_score": args.readiness,
        "ctl": args.ctl,
        "atl": args.atl,
        "tsb": args.tsb,
        "resting_heart_rate": 48,  # Default values
        "hrv": 65                 # Default values
    }
    
    if args.compare:
        # Run both modes for comparison
        print("\n🔄 RUNNING COMPARISON BETWEEN REASONING MODES")
        demo_with_scenario(use_llm=False, metrics=metrics, days_from_event=args.days_to_goal)
        demo_with_scenario(use_llm=True, llm_model=args.model, metrics=metrics, 
                           days_from_event=args.days_to_goal)
        print("\n📊 COMPARISON COMPLETE: Note the differences in explanation depth and contextual awareness")
    else:
        # Run single mode
        demo_with_scenario(use_llm=not args.no_llm, llm_model=args.model, metrics=metrics,
                          days_from_event=args.days_to_goal)
    
    print("\n📚 TIP: Run with --help to see all available options")
    print("🔄 TIP: Run with --compare to see both reasoning modes side by side")


if __name__ == "__main__":
    main()
