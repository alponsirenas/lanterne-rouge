import pandas as pd
import os
import json
import math
import datetime
from datetime import datetime, timedelta
from pathlib import Path

# Import Bannister model constants and functions from monitor.py
from src.lanterne_rouge.monitor import CTL_TC, ATL_TC, K_CTL, K_ATL

def run_bannister_over_csv(activities_file):
    """
    Process activities CSV file using the Bannister model to calculate CTL and ATL.
    
    Args:
        activities_file (str): Path to CSV file with activities data
    
    Returns:
        tuple: (ctl, atl) series with date index
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
        
        # Initialize the CTL and ATL series
        dates = []
        ctl_values = []
        atl_values = []
        ctl = atl = 0.0
        
        # Process each activity
        for _, row in enumerate(activities_df.iterrows()):
            _, row = row  # Unpack the row tuple
            
            # Get TSS from available columns
            tss = 0
            if 'relative_effort' in row and pd.notna(row['relative_effort']):
                tss = float(row['relative_effort'])
            elif 'suffer_score' in row and pd.notna(row['suffer_score']):
                tss = float(row['suffer_score'])
            elif 'icu_training_load' in row and pd.notna(row['icu_training_load']):
                tss = float(row['icu_training_load'])
            
            # Update CTL and ATL using the Bannister formula
            ctl += K_CTL * (tss - ctl)
            atl += K_ATL * (tss - atl)
            
            # Store values with the activity date
            dates.append(row['date'])
            ctl_values.append(ctl)
            atl_values.append(atl)
        
        # Create series with date index
        ctl_series = pd.Series(ctl_values, index=dates)
        atl_series = pd.Series(atl_values, index=dates)
        
        return ctl_series, atl_series
        
    except Exception as e:
        print(f"Error processing activities CSV: {str(e)}")
        raise

def test_ctl_atl_against_intervals_snapshot():
    """
    Test our Bannister implementation against reference values from intervals.icu.
    
    This test validates that our Bannister model implementation produces CTL/ATL values
    that closely match the reference values from intervals.icu (stored in wellness CSV).
    
    Note: Due to differences in implementation details between intervals.icu and our model,
    we allow for a higher error threshold for ATL which is more volatile (shorter time constant).
    """
    # Get the full path to the test data file
    test_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    wellness_path = test_dir / 'athlete_i296483_wellness.csv'
    
    # Read reference values from wellness CSV
    wellness_df = pd.read_csv(wellness_path)
    
    # Make sure we only work with rows that have valid CTL/ATL values
    wellness_df = wellness_df.dropna(subset=['ctl', 'atl'])
    
    # Convert wellness date to datetime and create a dictionary for quick lookup
    wellness_df['date'] = pd.to_datetime(wellness_df['date'])
    wellness_dict = {}
    for _, row in wellness_df.iterrows():
        date_key = row['date'].strftime('%Y-%m-%d')
        wellness_dict[date_key] = (row['ctl'], row['atl'])
    
    # Run our implementation on the activities data
    lr_ctl, lr_atl = run_bannister_over_csv('i296483_activities.csv')
    
    # Convert activity series to dictionary for comparison
    activities_dict = {}
    for date, ctl_val, atl_val in zip(lr_ctl.index, lr_ctl, lr_atl):
        date_key = date.strftime('%Y-%m-%d')
        # If there are multiple activities on the same day, use the last one
        activities_dict[date_key] = (ctl_val, atl_val)
    
    # Find overlapping dates
    common_dates = set(wellness_dict.keys()) & set(activities_dict.keys())
    
    if not common_dates:
        wellness_range = f"{min(wellness_dict.keys())} to {max(wellness_dict.keys())}"
        activity_range = f"{min(activities_dict.keys())} to {max(activities_dict.keys())}"
        assert False, (
            f"No overlapping dates found between wellness ({wellness_range}) "
            f"and activities ({activity_range}) data"
        )
    
    # Calculate errors for overlapping dates
    ctl_errors = []
    atl_errors = []
    
    for date in sorted(common_dates):
        wellness_ctl, wellness_atl = wellness_dict[date]
        activity_ctl, activity_atl = activities_dict[date]
        
        ctl_error = abs(wellness_ctl - activity_ctl)
        atl_error = abs(wellness_atl - activity_atl)
        
        ctl_errors.append(ctl_error)
        atl_errors.append(atl_error)
    
    # Calculate max errors
    max_ctl_error = max(ctl_errors) if ctl_errors else float('nan')
    max_atl_error = max(atl_errors) if atl_errors else float('nan')
    
    # Set thresholds based on expected accuracy
    # CTL (42-day time constant) should be very close between implementations
    # ATL (7-day time constant) can vary more due to its sensitivity to recent training
    assert max_ctl_error < 5.0, f"CTL maximum error ({max_ctl_error}) exceeds 5.0"
    assert max_atl_error < 30.0, f"ATL maximum error ({max_atl_error}) exceeds 30.0"