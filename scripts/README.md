# Lanterne Rouge Demo Scripts

This directory contains scripts for demonstrating and testing the Lanterne Rouge system.

## Demo Scripts

### `demo_enhanced.py` - Interactive Demo Experience

A user-friendly, colorful demo script with pre-defined scenarios to showcase the Lanterne Rouge system's capabilities. **Uses pre-recorded LLM responses - no API keys required!**

**Features:**
- Interactive CLI-based experience
- Pre-defined scenarios (normal training, fatigue, peak form, etc.)
- Comparison between LLM and rule-based reasoning
- Pre-recorded LLM responses (no API calls made)
- Detailed metrics display
- Colorful output formatting
- Completely self-contained demo

**Usage:**

```bash
# Run in interactive mode (recommended for first-time users)
python scripts/demo_enhanced.py --interactive

# Run a specific scenario
python scripts/demo_enhanced.py --scenario peak

# Compare LLM and rule-based reasoning for a scenario (uses pre-recorded responses)
python scripts/demo_enhanced.py --scenario fatigue --compare

# Use rule-based reasoning only
python scripts/demo_enhanced.py --no-llm

# All LLM scenarios use pre-recorded responses - no API key needed!
python scripts/demo_enhanced.py --scenario peak

# See all options
python scripts/demo_enhanced.py --help
```

### `demo.py` - Original Demo Script

The original demo script focused on command-line usage with customizable metrics.

**Usage:**

```bash
# Default demo with LLM reasoning
python scripts/demo.py

# Rule-based reasoning only
python scripts/demo.py --no-llm

# Compare both reasoning modes
python scripts/demo.py --compare

# Customize metrics
python scripts/demo.py --readiness 80 --ctl 65 --atl 60 --tsb 5

# Set days to goal event
python scripts/demo.py --days-to-goal 14
```

## Diagnostic Scripts

### `diagnose_bannister.py`

Validates the Bannister model calculations for CTL, ATL, and TSB.

### `test_power_tss.py`

Tests power-based Training Stress Score calculations.

### `test_tsb_parameters.py`

Tests TSB parameter configurations.

## Data Management Scripts

### `compare_data_sources.py`

Compares data from different sources for consistency.

### `compare_db_vs_calc.py`

Compares database values with calculated values.

### `export_strava_for_testing.py`

Exports Strava data for use in tests.

### `manage_memory_db.py`

Manages the SQLite memory database.

## Daily Operations

### `daily_run.py`

Main script for daily execution of the Lanterne Rouge system.

### `run_tour_coach.py`

Script for running the Tour Coach agent.

### `notify.py`

Sends email or SMS notifications with the daily recommendation.

## Utility Scripts

### `fix_lint_issues.py`

Fixes common linting issues in the codebase.

### `fix_trailing_whitespace.py`

Removes trailing whitespace from Python files.

### `update_athlete_ftp.py`

Updates athlete FTP values in the system.

### `update_github_secret.py`

Updates GitHub secrets for CI/CD workflows.
