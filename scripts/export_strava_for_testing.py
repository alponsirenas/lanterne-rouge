#!/usr/bin/env python
"""
Export recent Strava activities to a CSV file for testing purposes.
This helps synchronize test data with production data.
"""

import sys
import os
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add the src directory to Python path to find lanterne_rouge package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from lanterne_rouge.strava_api import strava_get

def export_activities_to_csv(days=90, output_file=None):
    """
    Export recent activities to a CSV file for testing.
    
    Args:
        days: Number of days to look back
        output_file: Path to the output file (default: tests/strava_export_YYYY-MM-DD.csv)
    """
    print(f"Exporting Strava activities for the past {days} days...")
    
    # Get activities from Strava
    activities = strava_get(f"athlete/activities?per_page=200")
    
    if not activities:
        print("No activities found.")
        return
    
    print(f"Found {len(activities)} activities.")
    
    # Set up output file
    if not output_file:
        today = datetime.now().strftime("%Y-%m-%d")
        output_file = Path(__file__).resolve().parents[1] / "tests" / f"strava_export_{today}.csv"
    
    # Get a list of all possible field names across all activities
    field_names = set()
    for activity in activities:
        if isinstance(activity, dict):
            field_names.update(activity.keys())
    
    # Sort field names for consistent output
    field_names = sorted(field_names)
    
    # Write activities to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        
        # Filter and write activities
        today = datetime.now().replace(tzinfo=None)
        cutoff = today - timedelta(days=days)
        
        exported_count = 0
        for activity in activities:
            if not isinstance(activity, dict):
                continue
                
            # Parse the start date
            try:
                start_date = activity.get("start_date_local")
                if not start_date:
                    continue
                    
                # Parse ISO 8601 date
                try:
                    act_dt = datetime.fromisoformat(start_date)
                    # Strip timezone info if present
                    if act_dt.tzinfo is not None:
                        act_dt = act_dt.replace(tzinfo=None)
                except ValueError:
                    # Fallback for legacy "Z" suffix
                    act_dt = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
                    
                # Skip activities older than cutoff
                if act_dt < cutoff:
                    continue
                
                # Write activity to CSV
                writer.writerow(activity)
                exported_count += 1
                
            except Exception as e:
                print(f"Error processing activity: {e}")
                continue
    
    print(f"Exported {exported_count} activities to {output_file}")
    return output_file

if __name__ == "__main__":
    # Get command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Export recent Strava activities to CSV for testing")
    parser.add_argument("--days", type=int, default=90, help="Number of days to look back")
    parser.add_argument("--output", type=str, help="Output file path")
    args = parser.parse_args()
    
    export_activities_to_csv(days=args.days, output_file=args.output)
