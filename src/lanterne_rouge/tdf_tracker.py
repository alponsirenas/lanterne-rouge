"""
TDF Points Tracker - Manages TDF simulation points and achievement data.

This module provides functionality to track points, stages, and bonuses
for the Tour de France Indoor Simulation in an LLM-powered system.
"""

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Any, Optional


class TDFTracker:
    """Manages TDF simulation points tracking and achievement data."""
    
    def __init__(self, data_file: Optional[str] = None):
        """Initialize TDF tracker with data file path."""
        if data_file is None:
            data_file = "output/tdf_points.json"
        
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(exist_ok=True)
        self._data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Load TDF data from file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Return default structure
        return {
            "total_points": 0,
            "stages_completed": 0,
            "consecutive_stages": 0,
            "breakaway_count": 0,
            "gc_count": 0,
            "mountain_breakaway_count": 0,
            "bonuses_earned": [],
            "stages": {},  # date -> stage data
            "last_updated": None
        }
    
    def _save_data(self):
        """Save TDF data to file."""
        self._data["last_updated"] = datetime.now().isoformat()
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, indent=2)
    
    def get_points_status(self) -> Dict[str, Any]:
        """Get current points status."""
        return {
            "total_points": self._data["total_points"],
            "stages_completed": self._data["stages_completed"],
            "consecutive_stages": self._data["consecutive_stages"],
            "breakaway_count": self._data["breakaway_count"],
            "gc_count": self._data["gc_count"],
            "mountain_breakaway_count": self._data["mountain_breakaway_count"],
            "bonuses_earned": self._data["bonuses_earned"].copy()
        }
    
    def add_stage_completion(
        self,
        stage_date: date,
        stage_number: int,
        stage_type: str,
        ride_mode: str,
        points_earned: int,
        activity_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add a completed stage and calculate bonuses."""
        
        stage_key = stage_date.isoformat()
        
        # Check if stage already completed today
        if stage_key in self._data["stages"]:
            return {"error": "Stage already completed today"}
        
        # Add stage data
        stage_data = {
            "stage_number": stage_number,
            "stage_type": stage_type,
            "ride_mode": ride_mode,
            "points_earned": points_earned,
            "completed_at": datetime.now().isoformat(),
            "activity_data": activity_data or {}
        }
        
        self._data["stages"][stage_key] = stage_data
        
        # Update counters
        self._data["total_points"] += points_earned
        self._data["stages_completed"] += 1
        
        if ride_mode == "breakaway":
            self._data["breakaway_count"] += 1
            if stage_type in ["mountain", "mtn_itt"]:
                self._data["mountain_breakaway_count"] += 1
        elif ride_mode == "gc":
            self._data["gc_count"] += 1
        
        # Update consecutive stages
        self._update_consecutive_stages()
        
        # Check for new bonuses
        bonuses_earned = self._check_bonuses()
        
        # Save data
        self._save_data()
        
        return {
            "success": True,
            "stage_data": stage_data,
            "new_total": self._data["total_points"],
            "bonuses_earned": bonuses_earned
        }
    
    def _update_consecutive_stages(self):
        """Update consecutive stages counter."""
        # Get last few days to check for consecutive completion
        recent_dates = sorted([
            datetime.fromisoformat(d).date() 
            for d in self._data["stages"].keys()
        ])[-10:]  # Check last 10 days
        
        if not recent_dates:
            self._data["consecutive_stages"] = 0
            return
        
        # Count consecutive days from most recent
        consecutive = 1
        current_date = recent_dates[-1]
        
        for i in range(len(recent_dates) - 2, -1, -1):
            prev_date = recent_dates[i]
            if (current_date - prev_date).days == 1:
                consecutive += 1
                current_date = prev_date
            else:
                break
        
        self._data["consecutive_stages"] = consecutive
    
    def _check_bonuses(self) -> list:
        """Check for newly earned bonuses."""
        new_bonuses = []
        
        # 5 consecutive stages
        if (self._data["consecutive_stages"] >= 5 and 
            "consecutive_5" not in self._data["bonuses_earned"]):
            self._data["bonuses_earned"].append("consecutive_5")
            self._data["total_points"] += 5
            new_bonuses.append({"type": "consecutive_5", "points": 5})
        
        # 10 breakaway stages
        if (self._data["breakaway_count"] >= 10 and 
            "breakaway_10" not in self._data["bonuses_earned"]):
            self._data["bonuses_earned"].append("breakaway_10")
            self._data["total_points"] += 15
            new_bonuses.append({"type": "breakaway_10", "points": 15})
        
        # All mountains in breakaway (6 mountain stages)
        if (self._data["mountain_breakaway_count"] >= 6 and 
            "all_mountains_breakaway" not in self._data["bonuses_earned"]):
            self._data["bonuses_earned"].append("all_mountains_breakaway")
            self._data["total_points"] += 10
            new_bonuses.append({"type": "all_mountains_breakaway", "points": 10})
        
        # Final week complete (stages 16-21)
        final_week_stages = [s for s in self._data["stages"].values() 
                           if s["stage_number"] >= 16]
        if (len(final_week_stages) >= 6 and 
            "final_week_complete" not in self._data["bonuses_earned"]):
            self._data["bonuses_earned"].append("final_week_complete")
            self._data["total_points"] += 10
            new_bonuses.append({"type": "final_week_complete", "points": 10})
        
        # All GC mode (all 21 stages in GC)
        if (self._data["stages_completed"] >= 21 and 
            self._data["breakaway_count"] == 0 and
            "all_gc_mode" not in self._data["bonuses_earned"]):
            self._data["bonuses_earned"].append("all_gc_mode")
            self._data["total_points"] += 25
            new_bonuses.append({"type": "all_gc_mode", "points": 25})
        
        return new_bonuses
    
    def get_stage_info_for_date(self, stage_date: date) -> Optional[Dict[str, Any]]:
        """Get stage information for a specific date."""
        stage_key = stage_date.isoformat()
        return self._data["stages"].get(stage_key)
    
    def is_stage_completed_today(self, today: date) -> bool:
        """Check if today's stage is already completed."""
        return today.isoformat() in self._data["stages"]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get complete TDF summary."""
        return {
            "total_points": self._data["total_points"],
            "stages_completed": self._data["stages_completed"],
            "consecutive_stages": self._data["consecutive_stages"],
            "breakaway_count": self._data["breakaway_count"],
            "gc_count": self._data["gc_count"],
            "mountain_breakaway_count": self._data["mountain_breakaway_count"],
            "bonuses_earned": len(self._data["bonuses_earned"]),
            "bonus_details": self._data["bonuses_earned"].copy(),
            "last_updated": self._data["last_updated"]
        }


# Convenience functions for backward compatibility
def load_points_status() -> Dict[str, Any]:
    """Load TDF points status using default tracker."""
    tracker = TDFTracker()
    return tracker.get_points_status()


def save_stage_completion(
    stage_date: date,
    stage_number: int,
    stage_type: str,
    ride_mode: str,
    points_earned: int,
    activity_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Save stage completion using default tracker."""
    tracker = TDFTracker()
    return tracker.add_stage_completion(
        stage_date, stage_number, stage_type, ride_mode, points_earned, activity_data
    )