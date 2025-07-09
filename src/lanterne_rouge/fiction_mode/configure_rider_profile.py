#!/usr/bin/env python3
"""
Rider Profile Configuration Tool for Fiction Mode

Helps users create and customize their rider profile for Fiction Mode narratives.
"""

import sys
import json
import subprocess
from pathlib import Path

# Import from local module
from .rider_profile import RiderProfileManager, RiderProfile


def create_example_profile():
    """Create an example profile with your actual details"""
    return {
        "name": "Ana Luisa Ponsirenas",
        "literary_voice": "Tim Krabbé, The Rider - spare, intelligent, introspective prose with attention to calculation and atmosphere",
        "simulation_goal": "Complete the Tour de France 2025 indoor simulation with focus on immersive narrative experience over results. Emphasize inner dialogue, tactical calculation, and emotional journey through each stage.",
        "virtual_role_preferences": "GC contender mindset with tactical awareness, occasionally breakaway specialist, observer and calculator of race dynamics - rarely pure sprinter or domestique unless strategically necessary",
        "ftp": 128,
        "bio": "Experienced amateur cyclist riding indoors, fascinated by the psychology of the peloton and the mental chess game of professional cycling. Approaches each stage with thoughtful strategy, self-reflection, and honest assessment of capabilities.",
        "style_instructions": "Highlight inner dialogue, power calculations, and emotional responses. Always connect personal efforts to real stage events and race dynamics. Use spare, observational prose. Focus on tactical awareness, positioning, and the mental game. Include specific power/HR data when narratively relevant.",
        "current_notes": "Building aerobic base through Z2/Z3 work. Focusing on completion and story development rather than aggressive racing. Interested in the complete Tour experience and personal growth through the challenge.",
        "nationality": "Spanish",
        "team_context": "Independent rider with GC ambitions and storyteller mindset",
        "personal_mission": "To experience and narrate the complete Tour de France journey with honesty, introspection, and respect for the sport's complexity and beauty"
    }


def main():
    """Main CLI function"""
    manager = RiderProfileManager()
    
    print("🚴‍♀️ Fiction Mode Rider Profile Configuration")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        command = "status"
    
    if command == "create":
        # Create new profile from template
        profile = manager.create_default_profile()
        print(f"\n✅ Template profile created at: {manager.profile_path}")
        print("\n📝 Next steps:")
        print(f"   1. Edit the file: {manager.profile_path}")
        print("   2. Replace all [CUSTOMIZE:...] and [YOUR...] placeholders")
        print("   3. Run 'python scripts/configure_rider_profile.py validate' to check")
        
    elif command == "example":
        # Create example with your actual details
        example_profile = RiderProfile.from_dict(create_example_profile())
        manager.save_profile(example_profile)
        print(f"\n✅ Example profile created at: {manager.profile_path}")
        print("📝 This uses Ana Luisa's details as an example - customize as needed!")
        
    elif command == "edit":
        # Open profile in default editor
        if not manager.profile_path.exists():
            manager.create_default_profile()
        
        try:
            # Try to open with default system editor
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(manager.profile_path)])
            elif sys.platform == "linux":
                subprocess.run(["xdg-open", str(manager.profile_path)])
            elif sys.platform == "win32":
                subprocess.run(["notepad", str(manager.profile_path)])
            else:
                print(f"Please edit manually: {manager.profile_path}")
        except Exception as e:
            print(f"Could not open editor. Please edit manually: {manager.profile_path}")
            print(f"Error: {e}")
    
    elif command == "validate":
        # Check if profile is ready
        is_ready, message = manager.validate_profile_ready()
        
        if is_ready:
            profile = manager.load_profile()
            print(f"✅ Profile is ready!")
            print(f"👤 Rider: {profile.name}")
            print(f"🎯 Goal: {profile.simulation_goal[:100]}...")
            print(f"📍 Role: {profile.virtual_role_preferences[:80]}...")
        else:
            print(f"❌ Profile needs customization: {message}")
            print(f"📝 Edit: {manager.profile_path}")
    
    elif command == "show":
        # Display current profile
        if manager.profile_path.exists():
            profile = manager.load_profile()
            print(f"📄 Current Profile ({manager.profile_path}):")
            print("-" * 40)
            print(f"Name: {profile.name}")
            print(f"Voice: {profile.literary_voice}")
            print(f"Goal: {profile.simulation_goal}")
            print(f"Role: {profile.virtual_role_preferences}")
            print(f"FTP: {profile.ftp}W")
            print(f"Bio: {profile.bio}")
            print(f"Notes: {profile.current_notes}")
        else:
            print("❌ No profile found. Run 'create' first.")
    
    else:
        # Show status and help
        print("📊 Current Status:")
        
        if manager.profile_path.exists():
            is_ready, message = manager.validate_profile_ready()
            if is_ready:
                profile = manager.load_profile()
                print(f"✅ Profile ready: {profile.name}")
            else:
                print(f"⚠️  Profile needs customization: {message}")
        else:
            print("❌ No profile found")
        
        print(f"\n📍 Profile location: {manager.profile_path}")
        
        print("\n🛠️  Available commands:")
        print("   create   - Create template profile to customize")
        print("   example  - Create example profile with sample data")
        print("   edit     - Open profile in system editor") 
        print("   validate - Check if profile is ready")
        print("   show     - Display current profile")
        print("   status   - Show this help (default)")
        
        print("\n💡 Quick start:")
        print("   python scripts/configure_rider_profile.py example")
        print("   python scripts/configure_rider_profile.py edit")


if __name__ == "__main__":
    main()
