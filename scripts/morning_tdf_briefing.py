#!/usr/bin/env python3
"""
Morning TDF briefing script that provides LLM-powered ride mode recommendations
based on current readiness and TDF stage information.
"""

import sys
import os
from pathlib import Path
from datetime import date
import json

# Add project paths for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Import our modules
from lanterne_rouge.monitor import get_oura_readiness, get_ctl_atl_tsb
from lanterne_rouge.mission_config import bootstrap
from lanterne_rouge.tour_coach import TourCoach
from scripts.notify import send_email, send_sms


def load_points_status():
    """Load current TDF points status using TDF tracker."""
    from lanterne_rouge.tdf_tracker import TDFTracker
    tracker = TDFTracker()
    return tracker.get_points_status()


def generate_briefing():
    """Generate the morning TDF briefing using LLM-powered TourCoach."""
    try:
        # Get current metrics
        readiness, *_ = get_oura_readiness()
        ctl, atl, tsb = get_ctl_atl_tsb()
        
        metrics = {
            "readiness_score": readiness,
            "ctl": ctl,
            "atl": atl,
            "tsb": tsb
        }
        
        # Load mission configuration
        mission_cfg = bootstrap("missions/tdf_sim_2025.toml")
        
        # Check if TDF is enabled and active
        today = date.today()
        
        # Load points status
        points_status = load_points_status()
        
        # Prepare TDF data
        tdf_data = {
            "points_status": points_status
        }
        
        # Create LLM-powered TourCoach
        use_llm = os.getenv("USE_LLM_REASONING", "true").lower() == "true"
        llm_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        
        coach = TourCoach(mission_cfg, use_llm_reasoning=use_llm, llm_model=llm_model)
        
        # Generate TDF recommendation
        briefing = coach.generate_tdf_recommendation(metrics, tdf_data)
        
        return briefing
        
    except Exception as e:
        return f"Error generating TDF briefing: {e}"


def main():
    """Main function to run morning TDF briefing."""
    print("� Generating LLM-Powered TDF Morning Briefing...")
    
    briefing = generate_briefing()
    
    # Save to file
    os.makedirs("output", exist_ok=True)
    with open("output/morning_tdf_briefing.txt", "w") as f:
        f.write(briefing)
    
    print("✅ Briefing generated: output/morning_tdf_briefing.txt")
    print("\n" + briefing)
    
    # Send notifications if configured
    email_recipient = os.getenv("TO_EMAIL")
    sms_recipient = os.getenv("TO_PHONE")
    
    if email_recipient:
        subject = f"� TDF Morning Briefing - Stage Ready!"
        send_email(subject, briefing, email_recipient)
        print(f"📧 Email sent to {email_recipient}")
    
    if sms_recipient:
        # Create short SMS version
        lines = briefing.split('\n')
        # Find key lines for SMS
        key_lines = []
        for line in lines[:15]:  # Look at first 15 lines
            if any(keyword in line.lower() for keyword in ['stage', 'recommendation', 'ride mode', 'points']):
                key_lines.append(line)
        
        sms_brief = '\n'.join(key_lines[:6])  # Max 6 key lines for SMS
        send_sms(sms_brief, sms_recipient, 
                use_twilio=os.getenv("USE_TWILIO", "false").lower() == "true")
        print(f"📱 SMS sent to {sms_recipient}")


if __name__ == "__main__":
    main()