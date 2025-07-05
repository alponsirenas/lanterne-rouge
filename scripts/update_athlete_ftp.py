#!/usr/bin/env python
"""
Script to update the athlete's FTP in the mission config.

Usage:
    python update_athlete_ftp.py <mission_id> <ftp_value>

Example:
    python update_athlete_ftp.py tdf-sim-2025 270
"""

import sys
import os
import json
import sqlite3
from pathlib import Path
import argparse

# Add the src directory to Python path to find lanterne_rouge package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from lanterne_rouge.mission_config import MissionConfig


def update_athlete_ftp(mission_id, ftp, db_path="memory/lanterne.db"):
    """Update the athlete FTP in the mission config."""
    db_path = Path(db_path)
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False

    try:
        # Connect to the database
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row

        # Retrieve the mission config
        row = con.execute("SELECT json FROM mission_config WHERE id = ?", (mission_id,)).fetchone()
        if row is None:
            print(f"Error: Mission '{mission_id}' not found in the database")
            con.close()
            return False

        # Parse the mission config
        mission_data = json.loads(row["json"])

        # Add athlete section if it doesn't exist
        if "athlete" not in mission_data:
            mission_data["athlete"] = {"ftp": ftp}
        else:
            mission_data["athlete"]["ftp"] = ftp

        # Update the mission config in the database
        con.execute(
            "UPDATE mission_config SET json = ? WHERE id = ?",
            (json.dumps(mission_data), mission_id)
        )
        con.commit()
        con.close()

        print(f"Successfully updated FTP to {ftp} watts for mission '{mission_id}'")
        return True

    except Exception as e:
        print(f"Error updating FTP: {e}")
        return False

def main():
    """Main function to parse arguments and update FTP."""
    parser = argparse.ArgumentParser(description="Update athlete's FTP in mission config")
    parser.add_argument("mission_id", help="ID of the mission to update")
    parser.add_argument("ftp", type=int, help="New FTP value in watts")
    parser.add_argument("--db", default="memory/lanterne.db", help="Path to the SQLite database")

    args = parser.parse_args()

    update_athlete_ftp(args.mission_id, args.ftp, args.db)

if __name__ == "__main__":
    main()
