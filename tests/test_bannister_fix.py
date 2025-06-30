import pandas as pd
import os
import json
import math
import datetime
from datetime import datetime, timedelta
from pathlib import Path

# Import Bannister model constants from monitor.py
CTL_TC = 42  # days
ATL_TC = 7   # days
K_CTL = 1 - math.exp(-1 / CTL_TC)
K_ATL = 1 - math.exp(-1 / ATL_TC)

def run_improved_bannister_over_csv(activities_file, target_date=None):
    """
    Process activities CSV file using the improved Bannister model to calculate CTL and ATL.
    
    Args:
        activities_file (str): Path to CSV file with activities data
        target_date (str, optional): Target date for CTL/ATL calculation in YYYY-MM-DD format
    
    Returns:
        tuple: (ctl, atl) values for the target date or latest date
    """
    # Get the full path to the test data file
    test_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    data_path = test_dir / activities_file
    
    try:
        # Process the activities CSV
        activities_df = pd.read_csv(data_path)
        
        # Make sure we have date information
        if 'start_date_local' in activities_df.columns:
            activities_df['date'] = pd.to_datetime(activities_df['start_date_local'])
        elif 'date' not in activities_df.columns:
            raise ValueError("No date column found in the activities CSV")
        else:
            activities_df['date'] = pd.to_datetime(activities_df['date'])
        
        # Sort by date
        activities_df = activities_df.sort_values('date')
        
        # Determine date range
        min_date = activities_df['date'].min().replace(tzinfo=None).date()
        if target_date:
            max_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            max_date = activities_df['date'].max().replace(tzinfo=None).date()
        
        # Use a 90-day lookback for more accurate CTL calculation
        start_date = (min_date - timedelta(days=0)).strftime("%Y-%m-%d")
        end_date = max_date.strftime("%Y-%m-%d")
        
        print(f"Analyzing activities from {start_date} to {end_date}")
        
        # Create daily TSS dictionary
        daily_tss = {}
        for _, row in activities_df.iterrows():
            # Get date in YYYY-MM-DD format
            date_key = row['date'].strftime('%Y-%m-%d')
            
            # Skip future dates if we're targeting a specific date
            if target_date and date_key > target_date:
                continue
                
            # Get TSS from available columns, prioritize icu_training_load
            tss = 0
            if 'icu_training_load' in row and pd.notna(row['icu_training_load']):
                tss = float(row['icu_training_load'])
            elif 'relative_effort' in row and pd.notna(row['relative_effort']):
                tss = float(row['relative_effort'])
            elif 'suffer_score' in row and pd.notna(row['suffer_score']):
                tss = float(row['suffer_score'])
            
            # Accumulate TSS for the day
            if date_key in daily_tss:
                daily_tss[date_key] += tss
            else:
                daily_tss[date_key] = tss
        
        # Get all dates in the range
        all_dates = []
        current = min_date
        while current <= max_date:
            all_dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
        
        # Create training load series with zeros for missing days
        tss_series = [daily_tss.get(date, 0) for date in all_dates]
        
        # Print recent daily loads for debugging
        print("\nRecent daily training loads:")
        last_n = min(10, len(all_dates))
        for i in range(-last_n, 0):
            if i+len(all_dates) >= 0:  # Prevent out of range
                date = all_dates[i]
                load = tss_series[i]
                print(f"  {date}: {load}")
        
        # Calculate CTL/ATL using the Bannister model
        ctl = atl = 0
        for tss in tss_series:
            # Use the equivalent formula: today = yesterday * decay + today's_value * (1 - decay)
            # Where decay = exp(-1/TC)
            ctl = ctl * (1 - K_CTL) + tss * K_CTL
            atl = atl * (1 - K_ATL) + tss * K_ATL
        
        print(f"\nFinal calculated values (for {all_dates[-1]}):")
        print(f"CTL: {ctl:.2f}")
        print(f"ATL: {atl:.2f}")
        print(f"TSB: {(ctl - atl):.2f}")
        
        return ctl, atl
        
    except Exception as e:
        print(f"Error processing activities CSV: {str(e)}")
        raise

def compare_with_intervals_icu(target_date=None):
    """
    Compare our Bannister calculations with intervals.icu data for a specific date
    
    Args:
        target_date (str, optional): Target date for comparison in YYYY-MM-DD format
    """
    test_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    wellness_path = test_dir / 'athlete_i296483_wellness.csv'
    
    # Read reference values from wellness CSV
    wellness_df = pd.read_csv(wellness_path)
    wellness_df['date'] = pd.to_datetime(wellness_df['date'])
    
    # Filter to target date if specified
    if target_date:
        target_dt = pd.to_datetime(target_date)
        wellness_row = wellness_df[wellness_df['date'] == target_dt]
        if len(wellness_row) == 0:
            print(f"No wellness data found for date {target_date}")
            return
    else:
        # Use the most recent date
        wellness_row = wellness_df.sort_values('date', ascending=False).iloc[0:1]
        target_date = wellness_row['date'].iloc[0].strftime('%Y-%m-%d')
    
    # Get intervals.icu values
    icu_ctl = wellness_row['ctl'].iloc[0]
    icu_atl = wellness_row['atl'].iloc[0]
    icu_tsb = icu_ctl - icu_atl
    
    print(f"\nIntervals.icu values for {target_date}:")
    print(f"CTL: {icu_ctl:.2f}")
    print(f"ATL: {icu_atl:.2f}")
    print(f"TSB: {icu_tsb:.2f}")
    
    # Run our implementation for the same date
    our_ctl, our_atl = run_improved_bannister_over_csv('i296483_activities.csv', target_date)
    our_tsb = our_ctl - our_atl
    
    print(f"\nOur calculated values for {target_date}:")
    print(f"CTL: {our_ctl:.2f}")
    print(f"ATL: {our_atl:.2f}")
    print(f"TSB: {our_tsb:.2f}")
    
    # Calculate differences
    ctl_diff = our_ctl - icu_ctl
    atl_diff = our_atl - icu_atl
    tsb_diff = our_tsb - icu_tsb
    
    print(f"\nDifferences (Our - intervals.icu):")
    print(f"CTL diff: {ctl_diff:.2f}")
    print(f"ATL diff: {atl_diff:.2f}")
    print(f"TSB diff: {tsb_diff:.2f}")

if __name__ == "__main__":
    # Compare values for June 23, 2025
    compare_with_intervals_icu('2025-06-23')
