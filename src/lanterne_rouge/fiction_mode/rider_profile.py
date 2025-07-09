"""
Rider Profile Management for Fiction Mode

Manages persistent rider identity, preferences, and mission context.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

import toml

from ..mission_config import get_cached_mission_config
from ..tdf_tracker import TDFTracker


@dataclass
class RiderProfile:
    """Persistent rider identity and preferences for Fiction Mode"""
    name: str
    literary_voice: str
    simulation_goal: str
    virtual_role_preferences: str
    ftp: Optional[int]
    bio: str
    style_instructions: str
    current_notes: str
    nationality: str = "Spanish"
    team_context: str = "Independent rider"
    personal_mission: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RiderProfile':
        """Create from dictionary"""
        return cls(**data)


class RiderProfileManager:
    """Manages rider profile persistence and mission integration"""
    
    def __init__(self, profile_path: Optional[str] = None):
        if profile_path is None:
            # Default to config directory
            self.profile_path = Path(__file__).parent.parent.parent.parent / "config" / "rider_profile.json"
        else:
            self.profile_path = Path(profile_path)
        
        # Ensure config directory exists
        self.profile_path.parent.mkdir(exist_ok=True)
    
    def is_profile_customized(self, profile: RiderProfile) -> bool:
        """Check if profile has been customized from template"""
        template_indicators = [
            "[YOUR NAME]",
            "[CUSTOMIZE:",
            "[YOUR NATIONALITY]"
        ]
        
        profile_text = json.dumps(profile.to_dict())
        return not any(indicator in profile_text for indicator in template_indicators)
    
    def validate_profile_ready(self) -> tuple[bool, str]:
        """Check if profile is ready for narrative generation"""
        profile = self.get_or_create_profile()
        
        if not self.is_profile_customized(profile):
            return False, f"Please customize your rider profile at: {self.profile_path}"
        
        if not profile.name or profile.name.strip() == "":
            return False, "Rider name is required"
            
        return True, "Profile ready"

    def get_or_create_profile(self) -> RiderProfile:
        """Get existing profile or create default from mission config"""
        
        if self.profile_path.exists():
            return self.load_profile()
        else:
            return self.create_default_profile()
    
    def load_profile(self) -> RiderProfile:
        """Load profile from JSON file"""
        try:
            with open(self.profile_path, 'r') as f:
                data = json.load(f)
            return RiderProfile.from_dict(data)
        except Exception as e:
            print(f"Failed to load rider profile: {e}")
            return self.create_default_profile()
    
    def save_profile(self, profile: RiderProfile) -> bool:
        """Save profile to JSON file"""
        try:
            with open(self.profile_path, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save rider profile: {e}")
            return False
    
    def create_default_profile(self) -> RiderProfile:
        """Create a template profile that should be customized by the user"""
        
        # Load mission config for context
        try:
            mission = get_cached_mission_config()
            if mission:
                ftp = mission.athlete.ftp if mission.athlete else 128
                goal_event = getattr(mission, 'goal_event', 'Tour de France Indoor Simulation 2025')
            else:
                ftp = 128
                goal_event = 'Tour de France Indoor Simulation 2025'
        except Exception:
            ftp = 128
            goal_event = 'Tour de France Indoor Simulation 2025'
        
        # Create template profile that users should customize
        profile = RiderProfile(
            name="[YOUR NAME]",
            literary_voice="Tim Krabbé, The Rider - spare, intelligent, introspective prose",
            simulation_goal=f"[CUSTOMIZE: Your goal for {goal_event}]",
            virtual_role_preferences="[CUSTOMIZE: GC contender, breakaway specialist, domestique, sprinter, etc.]",
            ftp=ftp,
            bio="[CUSTOMIZE: Your cycling background and approach]",
            style_instructions="[CUSTOMIZE: How you want your narratives to sound - inner dialogue, tactical focus, emotional depth, etc.]",
            current_notes="[CUSTOMIZE: Current training focus, goals, or personal notes]",
            nationality="[YOUR NATIONALITY]", 
            team_context="[CUSTOMIZE: Your virtual team or riding style]",
            personal_mission="[CUSTOMIZE: What this Tour means to you]"
        )
        
        # Save the template profile
        self.save_profile(profile)
        print(f"🎯 Created template rider profile at: {self.profile_path}")
        print("📝 Please edit this file to customize your cycling identity before generating narratives!")
        
        return profile
    
    def update_notes(self, new_notes: str) -> bool:
        """Update current notes in the profile"""
        profile = self.get_or_create_profile()
        profile.current_notes = new_notes
        return self.save_profile(profile)
    
    def get_context_for_agents(self, stage_number: Optional[int] = None) -> Dict[str, Any]:
        """Get complete context for agent prompts"""
        
        profile = self.get_or_create_profile()
        
        # Load TDF tracker data for simulation progress
        try:
            tdf_tracker = TDFTracker()
            tdf_status = tdf_tracker.get_summary()
            
            # Adjust status for the specific stage being generated
            if stage_number:
                # For historical stages, show the status as it would have been at that time
                adjusted_status = tdf_status.copy()
                adjusted_status['stages_completed'] = max(0, stage_number - 1)  # Stages completed BEFORE this stage
                adjusted_status['consecutive_stages'] = max(0, stage_number - 1)
                
                # Only show bonuses and points from stages before this one
                if stage_number == 1:
                    adjusted_status['total_points'] = 0
                    adjusted_status['bonuses_earned'] = 0
                    adjusted_status['breakaway_count'] = 0
                    adjusted_status['gc_count'] = 0
                
                tdf_status = adjusted_status
                
        except Exception as e:
            print(f"Warning: Could not load TDF tracker data: {e}")
            tdf_status = {
                "total_points": 0,
                "stages_completed": 0,
                "consecutive_stages": 0,
                "bonuses_earned": 0
            }
        
        # Load mission config for additional context
        try:
            mission = get_cached_mission_config()
            if mission:
                mission_context = {
                    'goal_event': getattr(mission, 'goal_event', 'Tour de France 2025'),
                    'goal_date': getattr(mission, 'goal_date', None),
                    'ftp': mission.athlete.ftp if mission.athlete else profile.ftp,
                    'targets': getattr(mission, 'targets', {}),
                    'constraints': getattr(mission, 'constraints', {})
                }
            else:
                mission_context = {'ftp': profile.ftp}
        except Exception:
            mission_context = {'ftp': profile.ftp}
        
        context = {
            'rider_profile': profile.to_dict(),
            'mission_context': mission_context,
            'tdf_simulation_status': tdf_status,
            'stage_context': {
                'stage_number': stage_number,
                'tour_year': 2025,
                'simulation_type': 'indoor_trainer'
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return context
    
    def format_context_for_prompt(self, stage_number: Optional[int] = None) -> str:
        """Format context as a string for LLM prompts"""
        
        context = self.get_context_for_agents(stage_number)
        profile = context['rider_profile']
        mission = context['mission_context']
        tdf_status = context['tdf_simulation_status']
        
        prompt_context = f"""
RIDER PROFILE:
Name: {profile['name']}
Literary Voice: {profile['literary_voice']}
Simulation Goal: {profile['simulation_goal']}
Role Preferences: {profile['virtual_role_preferences']}
FTP: {profile['ftp']}W
Bio: {profile['bio']}
Style Instructions: {profile['style_instructions']}
Current Notes: {profile['current_notes']}

MISSION CONTEXT:
Event: {mission.get('goal_event', 'Tour de France 2025')}
Target FTP: {mission.get('ftp', profile['ftp'])}W
Training Focus: {mission.get('targets', {})}

TDF SIMULATION PROGRESS:
Total Points: {tdf_status['total_points']}
Stages Completed: {tdf_status['stages_completed']}/21
Consecutive Stages: {tdf_status['consecutive_stages']}
Breakaway Count: {tdf_status.get('breakaway_count', 0)}
GC Mode Count: {tdf_status.get('gc_count', 0)}
Bonuses Earned: {tdf_status['bonuses_earned']} achievements
Achievement Details: {', '.join(tdf_status.get('bonus_details', []))}

STAGE CONTEXT:
Stage Number: {stage_number or 'Current'}
Tour Year: 2025
Simulation Type: Indoor trainer
"""
        
        return prompt_context.strip()


# Global instance for easy access
_profile_manager = None

def get_profile_manager() -> RiderProfileManager:
    """Get global profile manager instance"""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = RiderProfileManager()
    return _profile_manager

def get_rider_context(stage_number: Optional[int] = None) -> Dict[str, Any]:
    """Convenience function to get rider context"""
    return get_profile_manager().get_context_for_agents(stage_number)

def get_rider_prompt_context(stage_number: Optional[int] = None) -> str:
    """Convenience function to get formatted prompt context"""
    return get_profile_manager().format_context_for_prompt(stage_number)
