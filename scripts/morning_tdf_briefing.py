#!/usr/bin/env python3
"""
Morning TDF Briefing - Provides ride mode recommendation for today's stage.

Works alongside existing daily_run.py to add TDF-specific recommendations.
Usage: python scripts/morning_tdf_briefing.py
"""

import sys
import os
from pathlib import Path
from datetime import date
import json

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from lanterne_rouge.monitor import get_oura_readiness, get_ctl_atl_tsb
from scripts.notify import send_email, send_sms

# TDF Configuration (same as evening script)
TDF_START_DATE = date(2025, 7, 5)
POINTS_FILE = project_root / "output" / "tdf_points.json"

STAGE_TYPES = {
    1: 'flat', 2: 'hilly', 3: 'hilly', 4: 'flat', 5: 'hilly',
    6: 'mountain', 7: 'flat', 8: 'hilly', 9: 'mountain', 10: 'hilly',
    11: 'mountain', 12: 'hilly', 13: 'itt', 14: 'hilly', 15: 'mountain',
    16: 'mountain', 17: 'hilly', 18: 'mountain', 19: 'hilly', 20: 'mtn_itt', 21: 'flat'
}

POINTS_TABLE = {
    'flat': {'gc': 5, 'breakaway': 8},
    'hilly': {'gc': 7, 'breakaway': 11}, 
    'mountain': {'gc': 10, 'breakaway': 15},
    'itt': {'gc': 4, 'breakaway': 6},
    'mtn_itt': {'gc': 6, 'breakaway': 9}
}

def get_current_stage() -> tuple[int, str] | None:
    """Get current stage number and type."""
    today = date.today()
    days_elapsed = (today - TDF_START_DATE).days + 1
    
    if days_elapsed < 1 or days_elapsed > 21:
        return None
        
    stage_number = days_elapsed
    stage_type = STAGE_TYPES.get(stage_number)
    
    return stage_number, stage_type

def load_points_data() -> dict:
    """Load points data."""
    if POINTS_FILE.exists():
        with open(POINTS_FILE, 'r') as f:
            return json.load(f)
    return {
        "total_points": 0,
        "stages_completed": [],
        "consecutive_stages": 0,
        "breakaway_stages": 0,
        "gc_stages": 0,
        "bonuses_earned": []
    }

def recommend_ride_mode(readiness: int, tsb: float, stage_type: str, points_data: dict) -> tuple[str, str]:
    """Recommend ride mode based on current metrics."""
    
    # Safety first - force rest if severely fatigued
    if readiness < 60 or tsb < -20:
        return "rest", "Recovery needed - metrics indicate overreaching risk"
    
    # Conservative GC mode conditions
    if readiness < 75 or tsb < -10:
        gc_points = POINTS_TABLE[stage_type]['gc']
        return "gc", f"Conservative approach recommended for {gc_points} points - preserving energy with readiness at {readiness} and TSB at {tsb:.1f}"
    
    # Aggressive Breakaway mode conditions
    if readiness > 80 and tsb > -5:
        breakaway_points = POINTS_TABLE[stage_type]['breakaway']
        consecutive = points_data.get("consecutive_stages", 0)
        
        # Extra motivation for bonus opportunities
        if consecutive == 4:
            return "breakaway", f"GO FOR IT! Aggressive approach for {breakaway_points} points + you're 1 stage away from 5-consecutive bonus! Readiness {readiness}, TSB {tsb:.1f}"
        else:
            return "breakaway", f"Aggressive approach for {breakaway_points} points - good recovery state with readiness {readiness} and TSB {tsb:.1f}"
    
    # Balanced decision
    gc_points = POINTS_TABLE[stage_type]['gc']
    return "gc", f"Balanced approach for {gc_points} points - moderate fatigue state with readiness {readiness} and TSB {tsb:.1f}"

def generate_briefing(stage_number: int, stage_type: str, recommended_mode: str, 
                     rationale: str, readiness: int, tsb: float, points_data: dict) -> str:
    """Generate morning briefing."""
    
    # Calculate expected points
    if recommended_mode == "rest":
        expected_points = 0
    else:
        expected_points = POINTS_TABLE[stage_type][recommended_mode]
    
    lines = [
        f"🏆 TDF Stage {stage_number} - {stage_type.title()} Stage",
        "=" * 50,
        "",
        "📊 READINESS CHECK:",
        f"• Readiness Score: {readiness}/100",
        f"• TSB (Form): {tsb:.1f}",
        "",
        "🎯 TODAY'S RECOMMENDATION:",
        f"• Mode: {recommended_mode.upper()}",
        f"• Expected Points: {expected_points}",
        f"• Rationale: {rationale}",
        "",
        "📈 CURRENT STANDINGS:",
        f"• Total Points: {points_data['total_points']}",
        f"• Stages Completed: {len(points_data['stages_completed'])}/21",
        f"• Consecutive Stages: {points_data['consecutive_stages']}",
        f"• Breakaway Stages: {points_data['breakaway_stages']}",
        "",
        "🏆 BONUS OPPORTUNITIES:",
    ]
    
    # Add bonus progress
    consecutive = points_data['consecutive_stages']
    if consecutive >= 4:
        lines.append("   🔥 1 more stage for 5-consecutive bonus (+5 pts)")
    else:
        lines.append(f"   • 5 consecutive: {consecutive}/5")
    
    breakaway_count = points_data['breakaway_stages']
    if breakaway_count >= 9:
        lines.append("   🔥 1 more breakaway for 10-breakaway bonus (+15 pts)")
    else:
        lines.append(f"   • 10 breakaways: {breakaway_count}/10")
    
    # Mountain stages bonus
    mountain_stages = [6, 9, 11, 15, 16, 18]
    completed_mountains = [s for s in points_data['stages_completed'] if s in mountain_stages]
    if stage_number in mountain_stages:
        lines.append(f"   • All mountains breakaway: {len(completed_mountains)}/6 (TODAY COUNTS!)")
    else:
        lines.append(f"   • All mountains breakaway: {len(completed_mountains)}/6")
    
    lines.extend([
        "",
        "🚴 GET OUT THERE AND CRUSH IT! 💪"
    ])
    
    return "\n".join(lines)

def main():
    """Main morning briefing workflow."""
    print("🌅 TDF Morning Briefing")
    print("=" * 40)
    
    # Check if we're in TDF period
    stage_info = get_current_stage()
    if not stage_info:
        print("❌ Not currently in TDF simulation period")
        return
    
    stage_number, stage_type = stage_info
    
    # Get current metrics
    try:
        readiness, *_ = get_oura_readiness()
        ctl, atl, tsb = get_ctl_atl_tsb()
        
        if readiness is None or tsb is None:
            print("❌ Could not fetch readiness or fitness metrics")
            return
            
    except Exception as e:
        print(f"❌ Error fetching metrics: {e}")
        return
    
    # Load points data
    points_data = load_points_data()
    
    # Get recommendation
    recommended_mode, rationale = recommend_ride_mode(readiness, tsb, stage_type, points_data)
    
    # Generate briefing
    briefing = generate_briefing(
        stage_number, stage_type, recommended_mode, 
        rationale, readiness, tsb, points_data
    )
    
    print(briefing)
    
    # Send notification
    try:
        email_recipient = os.getenv("TO_EMAIL")
        sms_recipient = os.getenv("TO_PHONE")
        
        if email_recipient:
            send_email(f"🌅 TDF Stage {stage_number} Briefing", briefing, email_recipient)
            print("\n📧 Email briefing sent")
        
        if sms_recipient:
            # Short SMS version
            sms_briefing = f"🏆 Stage {stage_number} ({stage_type}): Recommend {recommended_mode.upper()} mode. Readiness {readiness}, TSB {tsb:.1f}. Expected: {POINTS_TABLE[stage_type].get(recommended_mode, 0)} pts"
            send_sms(sms_briefing, sms_recipient,
                    use_twilio=os.getenv("USE_TWILIO", "false").lower() == "true")
            print("📱 SMS briefing sent")
            
    except Exception as e:
        print(f"⚠️ Notification error: {e}")

if __name__ == "__main__":
    main()