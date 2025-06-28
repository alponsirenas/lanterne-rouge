#!/usr/bin/env python
"""
Reset or manipulate the Lanterne Rouge memory database.
This script helps isolate issues related to state persistence in the database.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to Python path to find lanterne_rouge package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))


def connect_to_db():
    """Connect to the memory database."""
    db_path = Path(__file__).resolve().parents[1] / "memory" / "lanterne.db"
    if not db_path.exists():
        print(f"Memory database not found at {db_path}")
        return None

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn, db_path


def show_db_contents(type_filter=None):
    """Show the contents of the memory database."""
    conn, db_path = connect_to_db()
    if not conn:
        return

    try:
        # Query with optional type filter
        query = "SELECT timestamp, type, data FROM memory"
        params = []

        if type_filter:
            query += " WHERE type = ?"
            params.append(type_filter)

        query += " ORDER BY timestamp DESC"

        # Execute query
        cursor = conn.execute(query, params)

        print(f"Database contents from {db_path}:")
        print("-" * 80)

        count = 0
        for row in cursor:
            count += 1
            ts = row["timestamp"]
            type_name = row["type"]

            try:
                data = json.loads(row["data"])
                data_summary = json.dumps(data, indent=2)
            except BaseException:
                data_summary = row["data"]

            print(f"Timestamp: {ts}")
            print(f"Type: {type_name}")
            print(f"Data: {data_summary}")
            print("-" * 80)

        print(f"Total entries: {count}")

    finally:
        conn.close()


def reset_database(confirm=False):
    """Reset the memory database by deleting all entries."""
    if not confirm:
        print("WARNING: This will delete all data in the memory database.")
        answer = input("Are you sure you want to continue? (yes/no): ")
        if answer.lower() != "yes":
            print("Operation cancelled.")
            return

    conn, db_path = connect_to_db()
    if not conn:
        return

    try:
        # Delete all entries
        conn.execute("DELETE FROM memory")
        conn.commit()
        print(f"Database reset complete. All entries removed from {db_path}")
    finally:
        conn.close()


def update_latest_observation(ctl=None, atl=None, tsb=None):
    """
    Update the most recent observation with new CTL, ATL, TSB values.
    Useful for testing different values without modifying the actual data source.
    """
    conn, db_path = connect_to_db()
    if not conn:
        return

    try:
        # Get the latest observation
        cursor = conn.execute(
            "SELECT timestamp, data FROM memory WHERE type='observation' ORDER BY timestamp DESC LIMIT 1"
        )
        row = cursor.fetchone()

        if not row:
            print("No observation found in the database.")
            return

        # Parse data
        timestamp = row["timestamp"]
        data = json.loads(row["data"])

        # Update values
        if ctl is not None:
            data["ctl"] = ctl
        if atl is not None:
            data["atl"] = atl
        if tsb is not None:
            data["tsb"] = tsb

        # Write back
        conn.execute(
            "UPDATE memory SET data=? WHERE timestamp=? AND type='observation'",
            (json.dumps(data), timestamp)
        )
        conn.commit()

        print(f"Updated observation at {timestamp}:")
        print(f"CTL={data['ctl']}, ATL={data['atl']}, TSB={data['tsb']}")

    finally:
        conn.close()


def main():
    """Parse command line arguments and run the appropriate function."""
    import argparse
    parser = argparse.ArgumentParser(description="Manage the Lanterne Rouge memory database")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Show database contents
    show_parser = subparsers.add_parser("show", help="Show database contents")
    show_parser.add_argument("--type", choices=["observation", "decision", "reflection"],
                             help="Filter by entry type")

    # Reset database
    reset_parser = subparsers.add_parser("reset", help="Reset the database")
    reset_parser.add_argument("--force", action="store_true",
                              help="Force reset without confirmation")

    # Update latest observation
    update_parser = subparsers.add_parser("update", help="Update latest observation")
    update_parser.add_argument("--ctl", type=float, help="New CTL value")
    update_parser.add_argument("--atl", type=float, help="New ATL value")
    update_parser.add_argument("--tsb", type=float, help="New TSB value")

    args = parser.parse_args()

    if args.command == "show":
        show_db_contents(args.type)
    elif args.command == "reset":
        reset_database(args.force)
    elif args.command == "update":
        update_latest_observation(args.ctl, args.atl, args.tsb)
    else:
        # Default to showing everything
        show_db_contents()


if __name__ == "__main__":
    main()
