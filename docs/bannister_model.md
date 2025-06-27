# Bannister Model Implementation

## Overview

The Bannister model, also known as the impulse-response model, is used to quantify training stress and calculate fitness (CTL), fatigue (ATL), and form (TSB) metrics. This document explains how Lanterne Rouge implements the model to match intervals.icu calculations.

## Key Metrics

- **CTL (Chronic Training Load)**: A measure of fitness, representing the long-term training load. Uses a 42-day time constant (standard in TrainingPeaks).
- **ATL (Acute Training Load)**: A measure of fatigue, representing the short-term training load. Uses a 7-day time constant (standard in TrainingPeaks).
- **TSB (Training Stress Balance)**: A measure of form/freshness, calculated as CTL - ATL.

## Implementation Details

The Bannister model is implemented in `src/lanterne_rouge/monitor.py` with the following key features:

### Time Constants

```python
CTL_TC = 42  # days - Standard time constant for Chronic Training Load
ATL_TC = 7   # days - Standard time constant for Acute Training Load
# Using the formula λ = 2/(N+1) as specified in TrainingPeaks documentation
K_CTL = 2 / (CTL_TC + 1)  # Lambda for CTL (Fitness)
K_ATL = 2 / (ATL_TC + 1)  # Lambda for ATL (Fatigue)
```

These decay constants use the TrainingPeaks standard formula of `λ = 2/(N+1)` where N is the time constant.

### Training Stress Score (TSS) Sources

The system uses multiple sources for training stress, with a priority order:

1. **Power-based TSS** (highest priority): Calculated using power data when available
   - Formula: `TSS = (duration_seconds × NP × IF) / (FTP × 3600) × 100`, where `IF = NP/FTP`
   - NP (Normalized Power): Taken from `weighted_average_watts` or falling back to `average_watts`
   - Uses athlete's FTP (Functional Threshold Power) from mission configuration

2. **Heart rate-based metrics** (second priority): From Strava's `relative_effort` or `suffer_score`

3. **Intervals.icu training load** (fallback): Used only when no other metrics are available

This prioritization ensures we use the most accurate training load metric available, similar to how Strava and TrainingPeaks calculate TSB/Form.

### FTP Configuration

The athlete's FTP is configured in the mission TOML file:

```toml
[athlete]
ftp = 250  # Athlete's Functional Threshold Power in watts
```

This provides a user-specific FTP value for accurate power-based TSS calculation. The implementation always fetches the most current FTP value from the mission config for every calculation, ensuring that any updates to FTP are immediately reflected in all TSS calculations. If no value is provided in the mission config, the system falls back to the `USER_FTP` environment variable, or a default of 250 watts.

To update the athlete's FTP, you can use the provided utility script:
```bash
python scripts/update_athlete_ftp.py <mission_id> <new_ftp>
```

For example:
```bash
python scripts/update_athlete_ftp.py tdf-sim-2025 250
```

This script updates both the TOML file and the cached database value to ensure consistent FTP usage across the system.

### Calculation Method

The model uses exponential decay to calculate CTL and ATL following the TrainingPeaks formula:

```python
# For each day's training load (tss)
new_ctl = ctl * (1 - K_CTL) + tss * K_CTL
new_atl = atl * (1 - K_ATL) + tss * K_ATL
```

#### Starting Values

The initial CTL and ATL values are important for accurate calculations. Instead of starting at zero, which would produce unrealistic values at the beginning, we use the average TSS from the first 14 days of data:

```python
# Initialize with average of first 14 days
init_period = min(14, len(tss_series))
if init_period > 0:
    avg_tss = sum(tss_series[:init_period]) / init_period
    ctl = atl = avg_tss
else:
    ctl = atl = 0.0
```

This approach provides more realistic starting values and ensures the model stabilizes faster.

### TSB (Form) Calculation

TSB (Training Stress Balance or Form) is calculated using today's CTL and ATL values:

```python
# TSB = Today's Fitness (CTL) - Today's Fatigue (ATL)
tsb = ctl - atl
```

This follows the TrainingPeaks and Strava definition where:
- A positive TSB indicates the athlete is fresh/over-adapted to the training load
- A neutral TSB indicates the athlete is adapted to the training load
- A negative TSB indicates the athlete is not yet adapted to the training load

Using the previous day's values better represents the athlete's form by comparing how they've historically trained (yesterday's CTL) to their recent training stress (yesterday's ATL), which aligns with how athletes experience freshness in real-world training.

### Lookback Period

The model uses a 90-day lookback period to allow for accurate CTL calculation, since CTL has a 42-day time constant.

## Testing 

Testing the Bannister model implementation involves comparing our calculations against intervals.icu reference values using:

1. Unit tests with fixed data in `tests/test_bannister.py`
2. A standalone test script `tests/test_bannister_fix.py` for detailed comparison
3. The new diagnostic tools described below

## Diagnostic Tools

Several diagnostic tools have been created to help troubleshoot and validate the Bannister model implementation:

### 1. Bannister Model Diagnostics (`scripts/diagnose_bannister.py`)

This script provides comprehensive diagnostics for the Bannister model calculations:

- Runs the production calculation method
- Checks recent values stored in the memory database
- Performs a manual calculation using current Strava data
- Compares implementation against intervals.icu reference values

Usage:
```bash
python scripts/diagnose_bannister.py
```

### 2. Strava Export Tool (`scripts/export_strava_for_testing.py`)

Exports recent Strava activities to a CSV file for testing purposes, helping synchronize test data with production data:

```bash
python scripts/export_strava_for_testing.py --days 90 --output custom_output.csv
```

### 3. Memory Database Management (`scripts/manage_memory_db.py`)

Manages the Lanterne Rouge memory database to isolate issues related to persisted state:

- Show database contents: `python scripts/manage_memory_db.py show`
- Reset the database: `python scripts/manage_memory_db.py reset`
- Update latest observation: `python scripts/manage_memory_db.py update --ctl 30 --atl 40 --tsb -10`

## Troubleshooting

If you observe discrepancies between expected and actual values:

1. Use the diagnostic tools to identify where the discrepancy originates
2. Check that the data sources (Strava activities) are consistent
3. Verify that the calculation methodology matches intervals.icu
4. Ensure no unexpected state persists in the memory database

When running tests, remember that the time periods must match - comparing different date ranges will naturally produce different results.

The model is validated against intervals.icu reference values using test data stored in:
- `tests/i296483_activities.csv`: Historical activity data
- `tests/athlete_i296483_wellness.csv`: Reference CTL/ATL values from intervals.icu

The test in `tests/test_bannister.py` verifies that our implementation produces values that closely match the reference values.

## Typical Values

- CTL: ~20-80 (higher for more trained athletes)
- ATL: Can spike higher than CTL after intense training blocks
- TSB: Typically ranges from -30 (high fatigue) to +20 (well-rested)

## References

- [Training Load and the Bannister Impulse-Response Model](https://www.trainingpeaks.com/learn/articles/the-science-of-the-performance-manager)
- [Intervals.icu Fitness & Freshness Metrics](https://intervals.icu/help#fitness-and-freshness)
