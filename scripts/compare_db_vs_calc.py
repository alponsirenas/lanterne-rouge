#!/usr/bin/env python
"""
This script compares Bannister model calculations with what's stored in the memory database.
It helps identify if the discrepancy is in the calculation or in how values are stored/retrieved.
"""

import sys
import os
import json
import sqlite3
import math
from datetime import datetime, timedelta
from pathlib import Path

# Add the src directory to Python path to find lanterne_rouge package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from lanterne_rouge.strava_api import strava_get
from lanterne_rouge.monitor import CTL_TC, ATL_TC

# Define constants
K_CTL = 1 - math.exp(-1 / CTL_TC)
K_ATL = 1 - math.exp(-1 / ATL_TC)

def get_latest_observation():
    """Get the latest observation from the memory database."""
    db_path = Path(__file__).resolve().parents[1] / "memory" / "lanterne.db"
    if not db_path.exists():
        print(f"Memory database not found at {db_path}")
        return None
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Get the latest observation
    cursor = conn.execute(
        "SELECT timestamp, data FROM memory WHERE type='observation' ORDER BY timestamp DESC LIMIT 1"
    )
    row = cursor.fetchone()
    
    if not row:
        print("No observation found in the database.")
        return None
        
    # Parse data
    timestamp = row["timestamp"]
    data = json.loads(row["data"])
    
    conn.close()
    
    return timestamp, data

def recalculate_bannister():
    """Recalculate the Bannister model values using the same logic as monitor.py."""
    print("Recalculating Bannister model values...")
    
    # Get activities from Strava
    activities = strava_get("athlete/activities?per_page=200")
    if not activities:
        print("No activities found.")
        return None, None, None
    
    print(f"Found {len(activities)} activities.")
    
    # Use naive datetimes consistently
    today = datetime.now().replace(tzinfo=None)
    days = 90
    start_day = today - timedelta(days=days)
    daily_tss = {}
    
    # Aggregate TSS per local day
    for act in activities:
        if not isinstance(act, dict):
            continue
            
        start_local = act.get("start_date_local")
        if not start_local:
            continue
            
        # Parse date
        try:
            act_dt = datetime.fromisoformat(start_local)
            # Strip timezone info if present
            if act_dt.tzinfo is not None:
                act_dt = act_dt.replace(tzinfo=None)
        except ValueError:
            # Fallback for legacy "Z" suffix
            try:
                act_dt = datetime.strptime(start_local, "%Y-%m-%dT%H:%M:%SZ")
            except:
                print(f"Could not parse date: {start_local}")
                continue
                
        if act_dt < start_day:
            continue
            
        # Get day key
        day_key = act_dt.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d")
        
        # Prioritize icu_training_load
        if 'icu_training_load' in act and act['icu_training_load'] is not None:
            effort = float(act['icu_training_load'])
        else:
            effort = act.get("relative_effort") or act.get("suffer_score") or 0
            
        daily_tss[day_key] = daily_tss.get(day_key, 0) + effort
    
    # Create a sorted list of dates
    date_range = [(start_day + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    
    # Create training load series
    tss_series = [daily_tss.get(day, 0) for day in date_range]
    
    # Print recent training loads
    print("\nRecent daily training loads:")
    for i in range(-10, 0):
        print(f"  {date_range[i]}: {tss_series[i]}")
    
    # Calculate CTL/ATL
    ctl = atl = 0.0
    for tss in tss_series:
        ctl = ctl * (1 - K_CTL) + tss * K_CTL
        atl = atl * (1 - K_ATL) + tss * K_ATL
    
    tsb = ctl - atl
    
    print(f"\nRecalculated values:")
    print(f"CTL: {ctl:.1f}")
    print(f"ATL: {atl:.1f}")
    print(f"TSB: {tsb:.1f}")
    
    return round(ctl, 1), round(atl, 1), round(tsb, 1)

def main():
    """Main function to compare database values with recalculation."""
    print("=== MEMORY DB VS RECALCULATION COMPARISON ===")
    
    # Get latest observation
    result = get_latest_observation()
    if not result:
        return
        
    timestamp, data = result
    
    print(f"Latest observation from {timestamp}:")
    print(f"CTL: {data.get('ctl')}")
    print(f"ATL: {data.get('atl')}")
    print(f"TSB: {data.get('tsb')}")
    
    # Recalculate using the same logic
    ctl, atl, tsb = recalculate_bannister()
    
    # Compare values
    if ctl is not None and data.get('ctl') is not None:
        print("\nDifferences (Recalculated - Database):")
        print(f"CTL diff: {ctl - data.get('ctl'):.1f}")
        print(f"ATL diff: {atl - data.get('atl'):.1f}")
        print(f"TSB diff: {tsb - data.get('tsb'):.1f}")
    
if __name__ == "__main__":
    main()
