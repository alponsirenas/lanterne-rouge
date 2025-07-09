#!/usr/bin/env python3
"""
Lanterne Rouge Interactive Demo

An enhanced demo script for the Lanterne Rouge system that provides:
1. A guided demonstration of core features
2. Pre-defined scenarios to showcase different training situations
3. Interactive CLI-based experience
4. Easy comparison between LLM and rule-based reasoning modes
5. Pre-recorded LLM responses (no API calls required)

This demo is completely self-contained and doesn't require any API keys or 
external services. LLM responses are pre-recorded to showcase the system's
capabilities without making actual API calls.

Usage:
    python scripts/demo_enhanced.py --interactive    # Recommended for first time
    python scripts/demo_enhanced.py --scenario peak  # Run specific scenario
    python scripts/demo_enhanced.py --compare        # Compare reasoning modes
    python scripts/demo_enhanced.py --help           # Show all options
"""
import os
import sys
from datetime import date, timedelta
import argparse
from pathlib import Path
import time
import random
import traceback
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

# Get Lanterne Rouge version
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from src.lanterne_rouge.tour_coach import get_version
    VERSION = get_version()
except ImportError:
    VERSION = "0.4.0"  # Default if import fails

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lanterne_rouge.mission_config import bootstrap, MissionConfig
from src.lanterne_rouge.tour_coach import TourCoach
from src.lanterne_rouge.reasoner import ReasoningAgent, TrainingDecision
from src.lanterne_rouge.plan_generator import WorkoutPlanner
from src.lanterne_rouge.ai_clients import CommunicationAgent
from src.lanterne_rouge.memory_bus import log_observation, log_decision, log_reflection


class DemoReasoningAgent(ReasoningAgent):
    """Custom reasoning agent that uses pre-recorded LLM responses for demos."""
    
    def __init__(self, use_llm: bool = True, model: str = None, demo_scenario: str = None):
        super().__init__(use_llm, model)
        self.demo_scenario = demo_scenario
    
    def _make_llm_decision(self, metrics, mission_config=None, current_date=None):
        """Override to use pre-recorded responses instead of API calls."""
        if self.demo_scenario and self.demo_scenario in DEMO_LLM_RESPONSES:
            response_data = DEMO_LLM_RESPONSES[self.demo_scenario]
            return TrainingDecision(
                action=response_data["action"],
                reason=response_data["reason"],
                intensity_recommendation=response_data["intensity_recommendation"],
                flags=response_data["flags"],
                confidence=response_data["confidence"]
            )
        else:
            # Fallback to rule-based for scenarios without pre-recorded responses
            return self._make_rule_based_decision(metrics, mission_config, current_date)


class DemoTourCoach(TourCoach):
    """Custom TourCoach subclass that supports date overriding and demo responses."""
    
    def __init__(self, config, use_llm_reasoning: bool = True, llm_model: str = None, demo_scenario: str = None):
        """Initialize with demo scenario for pre-recorded responses."""
        self.config = config
        self.reasoning_agent = DemoReasoningAgent(use_llm=use_llm_reasoning, model=llm_model, demo_scenario=demo_scenario)
        self.workout_planner = WorkoutPlanner(config)
        self.communication_agent = CommunicationAgent()
    
    def generate_daily_recommendation(self, metrics, demo_date=None):
        """Generate a complete daily training recommendation with an optional demo date."""
        current_date = demo_date or date.today()
        training_phase = self.config.training_phase(current_date)

        # Step 1: Make training decision (with mission config and date for LLM context)
        decision = self.reasoning_agent.make_decision(metrics, self.config, current_date)

        # Step 2: Generate workout plan
        workout = self.workout_planner.generate_workout(decision, training_phase)

        # Step 3: Generate natural language summary
        summary = self.communication_agent.generate_summary(
            decision, workout, metrics, self.config, current_date
        )

        # Log to memory
        log_observation(metrics)
        log_decision({
            "action": decision.action,
            "reason": decision.reason,
            "confidence": decision.confidence
        })
        log_reflection({"summary": summary})

        return summary


# Pre-recorded LLM responses for demo scenarios
DEMO_LLM_RESPONSES = {
    "normal": {
        "action": "maintain",
        "reason": "Looking at your current metrics, you're in a really good spot right now! Your readiness score of 80 shows you're well-recovered, and your TSB of 5 indicates you have a nice balance between fitness and fatigue. With 45 days until your goal event, we're in the perfect window to maintain this steady progress. Your CTL of 60 shows you've built a solid aerobic foundation, and your ATL of 55 suggests you're managing your training load well. This is exactly where we want to be during the base phase - building sustainable fitness without overdoing it. Let's keep this momentum going with a solid endurance ride that will continue to develop your aerobic engine while respecting your current recovery state.",
        "intensity_recommendation": "moderate",
        "flags": [],
        "confidence": 0.85
    },
    "fatigue": {
        "action": "recover",
        "reason": "I can see from your metrics that you're carrying quite a bit of fatigue right now, and your body is telling us it needs some recovery time. Your readiness score of 60 is below your typical range, and more importantly, your TSB of -15 shows you've been pushing hard recently and accumulated significant fatigue. While your CTL of 70 demonstrates you've built excellent fitness, your ATL of 85 indicates the recent training load has been quite high. With 30 days until your goal, we have time to be smart about this. Taking a recovery day now will help you bounce back stronger and avoid the risk of overreaching. Think of this as an investment in your future performance - by recovering properly today, you'll be able to handle higher quality training sessions in the coming weeks.",
        "intensity_recommendation": "low",
        "flags": ["low_readiness", "negative_tsb"],
        "confidence": 0.9
    },
    "peak": {
        "action": "maintain",
        "reason": "You're in absolutely fantastic form right now! Your readiness score of 90 shows you're firing on all cylinders, and your TSB of 10 indicates you've achieved that sweet spot where you're fresh but still maintaining your fitness. With just 7 days until your goal event, this is exactly where we want to be. Your CTL of 75 shows you've built excellent fitness over your training cycle, and the fact that your ATL has dropped to 65 means the taper is working perfectly. At this point, our job is to maintain this peak condition without disrupting the delicate balance you've achieved. A moderate effort today will keep your systems primed and ready while avoiding any unnecessary fatigue that could compromise your performance on race day.",
        "intensity_recommendation": "moderate",
        "flags": ["peak_form"],
        "confidence": 0.95
    },
    "recovery": {
        "action": "maintain",
        "reason": "You're in a really good recovery phase right now, and your metrics show that the planned recovery period is working well. Your readiness score of 75 is solid, and your TSB of 18 indicates you've successfully reduced fatigue while maintaining your fitness base. Your CTL of 68 shows you haven't lost significant fitness during this recovery block, which is exactly what we want to see. With 21 days until your goal, this recovery week is perfectly timed to set you up for the final build phase. Your body is responding well to the reduced load, and we can see from your HRV and resting heart rate that you're adapting positively. Let's continue with moderate efforts that maintain your aerobic base while keeping you fresh for the harder training to come.",
        "intensity_recommendation": "moderate",
        "flags": ["recovery_phase"],
        "confidence": 0.8
    },
    "overtraining": {
        "action": "recover",
        "reason": "Your metrics are showing some concerning signs that we need to address immediately. A readiness score of 50 combined with a TSB of -25 indicates you're in a state of significant overreaching that could progress to overtraining if we don't take action now. Your extremely high ATL of 100 compared to your CTL of 75 shows you've been pushing beyond what your body can currently handle. This isn't a reflection of your fitness or dedication - it's actually quite common when athletes are highly motivated and training hard. The key now is to step back and allow your body to recover properly. With 35 days until your goal, we have time to recover smartly and come back stronger. Taking several easy days or even complete rest will help restore your readiness and get your TSB back to a manageable level.",
        "intensity_recommendation": "low",
        "flags": ["overreaching", "very_negative_tsb", "low_readiness"],
        "confidence": 0.95
    },
    "taper": {
        "action": "ease",
        "reason": "We're in the critical final days before your goal event, and your metrics show you're responding well to the taper. Your readiness score of 85 is excellent, and your TSB of 12 indicates you're getting fresh while maintaining your hard-earned fitness. With your CTL at 72, you've clearly done the work to build a strong fitness foundation. Now, with just 3 days to go, our priority is maintaining that sharpness without adding any fatigue. Your body is primed and ready - the fitness gains from this point forward would be minimal, but the risk of accumulating fatigue is high. Today's session should be easy to moderate, focusing on keeping your legs moving and your systems activated without any meaningful stress. Trust the work you've done and focus on arriving at the start line feeling confident and fresh.",
        "intensity_recommendation": "low",
        "flags": ["taper_phase", "event_imminent"],
        "confidence": 0.9
    },
    "random": {
        "action": "maintain",
        "reason": "Based on your current metrics, I'm seeing a mixed picture that requires careful consideration. Your readiness and training load indicators suggest we need to balance maintaining your fitness with respecting your body's current state. Given the variability in your numbers, the safest approach is to proceed with a moderate effort that allows us to assess how you respond today. This will give us valuable information about your current form and help guide tomorrow's training decisions. Remember, every day of training is a data point that helps us optimize your approach to your goal event.",
        "intensity_recommendation": "moderate",
        "flags": ["variable_metrics"],
        "confidence": 0.7
    }
}

# Pre-defined scenarios to demonstrate different training situations
SCENARIOS = {
    "normal": {
        "name": "Normal Training Day",
        "description": "Standard day with good recovery and balanced training load",
        "metrics": {
            "readiness_score": 80,
            "ctl": 60,
            "atl": 55, 
            "tsb": 5,
            "resting_heart_rate": 45,
            "hrv": 70
        },
        "days_from_event": 45
    },
    "fatigue": {
        "name": "High Fatigue Day",
        "description": "Low readiness with accumulated fatigue and negative TSB",
        "metrics": {
            "readiness_score": 60,
            "ctl": 70,
            "atl": 85,
            "tsb": -15,
            "resting_heart_rate": 52,
            "hrv": 45
        },
        "days_from_event": 30
    },
    "peak": {
        "name": "Peak Form Day",
        "description": "Excellent readiness with positive TSB near an important event",
        "metrics": {
            "readiness_score": 90,
            "ctl": 75,
            "atl": 65,
            "tsb": 10,
            "resting_heart_rate": 42,
            "hrv": 85
        },
        "days_from_event": 7
    },
    "recovery": {
        "name": "Recovery Week",
        "description": "Planned recovery period with reduced training load",
        "metrics": {
            "readiness_score": 75,
            "ctl": 68,
            "atl": 50,
            "tsb": 18,
            "resting_heart_rate": 46,
            "hrv": 75
        },
        "days_from_event": 21
    },
    "overtraining": {
        "name": "Overtraining Warning",
        "description": "Very low readiness with extremely negative TSB",
        "metrics": {
            "readiness_score": 50,
            "ctl": 75,
            "atl": 100,
            "tsb": -25,
            "resting_heart_rate": 56,
            "hrv": 35
        },
        "days_from_event": 35
    },
    "taper": {
        "name": "Event Taper",
        "description": "Final preparation days before the goal event",
        "metrics": {
            "readiness_score": 85,
            "ctl": 72,
            "atl": 60,
            "tsb": 12,
            "resting_heart_rate": 44,
            "hrv": 80
        },
        "days_from_event": 3
    },
    "random": {
        "name": "Random Situation",
        "description": "Randomized metrics for unpredictable scenarios",
        "metrics": None,  # Will be generated randomly
        "days_from_event": None  # Will be generated randomly
    }
}


def print_header():
    """Display a stylish header for the demo."""
    print(f"\n{Fore.RED}{'=' * 80}")
    print(f"{Fore.YELLOW}{'*' * 30} LANTERNE ROUGE {'*' * 31}")
    print(f"{Fore.YELLOW}{'*' * 23} INTERACTIVE DEMO SYSTEM {'*' * 23}")
    print(f"{Fore.YELLOW}Version {VERSION}")
    print(f"{Fore.RED}{'=' * 80}\n")
    print(f"{Fore.CYAN}Named after the iconic 'lanterne rouge' — the rider who finishes last")
    print(f"at the Tour de France — this project embodies resilience, consistency,")
    print(f"and intelligent endurance. It's not about being first; it's about")
    print(f"finishing your own race, every stage, every day.\n")


def print_footer():
    """Display next steps and additional information at the end of the demo."""
    print(f"\n{Fore.BLUE}{'=' * 80}")
    print(f"{Fore.GREEN}NEXT STEPS:")
    print(f"{Fore.CYAN}1. Set up your environment with your API keys for the real system:")
    print(f"   - OPENAI_API_KEY for LLM-powered reasoning")
    print(f"   - OURA_ACCESS_TOKEN for readiness data")
    print(f"   - STRAVA_* credentials for activity data")
    print(f"\n{Fore.CYAN}2. Run the real system with your own data:")
    print(f"   python scripts/daily_run.py")
    print(f"\n{Fore.CYAN}3. Check out the documentation:")
    print(f"   - docs/architecture.md for system design")
    print(f"   - docs/bannister_model.md for CTL/ATL/TSB calculation details")
    print(f"   - RELEASE_NOTES_v0.4.0.md for latest changes")
    print(f"\n{Fore.YELLOW}Visit the GitHub project for more information:")
    print(f"https://github.com/alponsirenas/lanterne-rouge")
    print(f"\n{Fore.MAGENTA}Note: This demo used pre-recorded responses to showcase LLM capabilities.")
    print(f"The real system makes live API calls for dynamic, personalized reasoning.")
    print(f"{Fore.BLUE}{'=' * 80}")
    print(f"\n{Fore.GREEN}Thank you for exploring Lanterne Rouge v{VERSION}! 🚴‍♂️")


def generate_random_scenario():
    """Generate a random training scenario."""
    return {
        "readiness_score": random.randint(50, 95),
        "ctl": random.randint(40, 85),
        "atl": random.randint(35, 100), 
        "tsb": random.randint(-30, 20),
        "resting_heart_rate": random.randint(42, 58),
        "hrv": random.randint(35, 90)
    }, random.randint(3, 60)


def run_demo_scenario(scenario_key, use_llm=True, llm_model=None, verbose=False):
    """Run a specific demo scenario."""
    scenario = SCENARIOS[scenario_key]
    metrics = scenario["metrics"]
    days_from_event = scenario["days_from_event"]
    
    # Handle random scenario
    if scenario_key == "random":
        metrics, days_from_event = generate_random_scenario()
    
    # Load mission config
    config = bootstrap("missions/tdf_sim_2025.toml")
    
    # Calculate the demo date
    demo_date = config.goal_date - timedelta(days=days_from_event)
    
    # Create DemoTourCoach with specified configuration and scenario for pre-recorded responses
    coach = DemoTourCoach(config, use_llm_reasoning=use_llm, llm_model=llm_model, demo_scenario=scenario_key)
    
    # Display scenario information
    print(f"\n{Fore.BLUE}{'=' * 80}")
    print(f"{Fore.GREEN}SCENARIO: {scenario['name']}")
    print(f"{Fore.CYAN}{scenario['description']}")
    print(f"\n{Fore.YELLOW}📅 DATE: {demo_date} ({(config.goal_date - demo_date).days} days to goal)")
    print(f"🧠 REASONING: {'LLM-based' if use_llm else 'Rule-based'}")
    if llm_model and use_llm:
        print(f"🤖 MODEL: {llm_model}")
        
    # Add disclaimer for demo mode
    if use_llm:
        print(f"\n{Fore.BLUE}ℹ️  DEMO MODE: Using pre-recorded LLM responses. No API calls will be made.")
    else:
        print(f"\n{Fore.BLUE}ℹ️  DEMO MODE: Using rule-based reasoning only. No API calls will be made.")
    print()
    
    if verbose:
        print(f"\n{Fore.MAGENTA}DETAILED METRICS:{Style.RESET_ALL}")
        print(f"  Readiness Score: {metrics['readiness_score']} / 100")
        print(f"  Chronic Training Load (CTL): {metrics['ctl']}")
        print(f"  Acute Training Load (ATL): {metrics['atl']}")
        print(f"  Training Stress Balance (TSB): {metrics['tsb']}")
        print(f"  Resting Heart Rate: {metrics['resting_heart_rate']} bpm")
        print(f"  Heart Rate Variability: {metrics['hrv']} ms")
    else:
        print(f"{Fore.MAGENTA}METRICS: Readiness={metrics['readiness_score']}, CTL={metrics['ctl']}, " 
              f"ATL={metrics['atl']}, TSB={metrics['tsb']}{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}Generating recommendation...{Style.RESET_ALL}")
    
    # Simulate processing time for better UX
    time.sleep(1)
    
    # Generate recommendation with our custom demo date
    recommendation = coach.generate_daily_recommendation(metrics, demo_date=demo_date)
    
    print(f"\n{Fore.BLUE}{'-' * 80}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}COACH RECOMMENDATION:{Style.RESET_ALL}\n")
    print(recommendation)
    print(f"\n{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}")
    
    return recommendation


def interactive_demo():
    """Run the demo in interactive mode."""
    print_header()
    
    print(f"{Fore.GREEN}Welcome to the Lanterne Rouge Interactive Demo!")
    print("This demo will guide you through different training scenarios to showcase")
    print("how the Lanterne Rouge system adapts its recommendations based on your")
    print("fitness, fatigue, and readiness metrics.")
    print(f"\n{Fore.BLUE}ℹ️  This demo uses pre-recorded responses to show LLM capabilities")
    print("without requiring API keys or making external calls.\n")
    
    # Ask for reasoning mode
    print(f"\n{Fore.CYAN}REASONING MODE:")
    print("1. LLM-based reasoning (uses pre-recorded responses)")
    print("2. Rule-based reasoning (algorithmic decision making)")
    print("3. Compare both modes (see the difference)")
    
    while True:
        choice = input("\nSelect reasoning mode [1-3]: ")
        if choice in ['1', '2', '3']:
            use_llm = choice == '1' or choice == '3'
            compare_modes = choice == '3'
            break
        print("Please enter a valid option (1-3)")
    
    # Select scenario
    print(f"\n{Fore.CYAN}SELECT A SCENARIO:{Style.RESET_ALL}")
    i = 1
    scenario_options = {}
    for key, scenario in SCENARIOS.items():
        print(f"{i}. {scenario['name']} - {scenario['description']}")
        scenario_options[str(i)] = key
        i += 1
    
    while True:
        scenario_choice = input("\nSelect scenario [1-7]: ")
        if scenario_choice in scenario_options:
            selected_scenario = scenario_options[scenario_choice]
            break
        print(f"Please enter a valid option (1-{len(SCENARIOS)})")
    
    # Run the selected scenario
    if compare_modes:
        print(f"\n{Fore.YELLOW}Running comparison between rule-based and LLM reasoning...{Style.RESET_ALL}")
        print(f"\n{Fore.MAGENTA}RULE-BASED REASONING:{Style.RESET_ALL}")
        rule_based_result = run_demo_scenario(selected_scenario, use_llm=False, verbose=True)
        
        print(f"\n{Fore.MAGENTA}LLM-BASED REASONING:{Style.RESET_ALL}")
        llm_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        llm_result = run_demo_scenario(selected_scenario, use_llm=True, llm_model=llm_model, verbose=True)
        
        print(f"\n{Fore.GREEN}COMPARISON COMPLETE{Style.RESET_ALL}")
        print("Note the differences in explanation depth, personalization, and contextual awareness.")
    else:
        llm_model = None
        if use_llm:
            llm_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        run_demo_scenario(selected_scenario, use_llm=use_llm, llm_model=llm_model, verbose=True)
    
    print(f"\n{Fore.GREEN}Demo complete! 🏁{Style.RESET_ALL}")
    print("This demonstrates how Lanterne Rouge adapts its recommendations based on")
    print("your current metrics and training context.")
    
    # Ask if they want to try another scenario
    retry = input("\nWould you like to try another scenario? (y/n): ")
    if retry.lower() == 'y':
        interactive_demo()
    else:
        print_footer()


def main():
    """Main function for running the demo."""
    parser = argparse.ArgumentParser(description="Lanterne Rouge Enhanced Demo")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Run in interactive guided mode (recommended for first-time users)")
    parser.add_argument("--scenario", "-s", choices=list(SCENARIOS.keys()),
                       help="Specific scenario to run (normal, fatigue, peak, recovery, overtraining, taper, random)")
    parser.add_argument("--no-llm", action="store_true", 
                       help="Use rule-based reasoning only")
    parser.add_argument("--model", type=str, default="gpt-4-turbo-preview", 
                       help="LLM model name to display (demo uses pre-recorded responses)")
    parser.add_argument("--compare", "-c", action="store_true", 
                       help="Run both LLM and rule-based modes for comparison")
    parser.add_argument("--metrics", type=str, 
                       help="Custom metrics in JSON format (advanced)")
    parser.add_argument("--days-to-goal", type=int, 
                       help="Custom days until goal event (1-60)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Show detailed metrics information")
    args = parser.parse_args()
    
    # Run in interactive mode if specified
    if args.interactive:
        interactive_demo()
        return
    
    # If no scenario specified but not interactive, show the header and default to "normal"
    if not args.scenario:
        print_header()
        args.scenario = "normal"
        print(f"{Fore.YELLOW}No scenario specified. Using the default 'normal' scenario.")
        print(f"Run with --interactive for a guided experience or --help for more options.\n")
    
    # Run comparison if requested
    if args.compare:
        print(f"{Fore.YELLOW}Running comparison between rule-based and LLM reasoning...{Style.RESET_ALL}")
        run_demo_scenario(args.scenario, use_llm=False, verbose=args.verbose)
        run_demo_scenario(args.scenario, use_llm=True, llm_model=args.model, verbose=args.verbose)
        print(f"\n{Fore.GREEN}COMPARISON COMPLETE{Style.RESET_ALL}")
        print("Note the differences in explanation depth, personalization, and contextual awareness.")
    else:
        run_demo_scenario(args.scenario, use_llm=not args.no_llm, 
                        llm_model=args.model, verbose=args.verbose)
        print_footer()


if __name__ == "__main__":
    try:
        main()
        if not any(sys.argv[1:]):  # No command line arguments
            print_footer()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}Demo interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n{Fore.RED}An error occurred: {e}")
        print(f"{Fore.YELLOW}For detailed error information:")
        traceback.print_exc()
        sys.exit(1)
