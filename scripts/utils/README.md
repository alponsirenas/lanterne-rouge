# Scripts Utilities

This directory contains utility and diagnostic scripts used for maintenance, debugging, and data analysis.

## Diagnostic Scripts
- `diagnose_bannister.py` - Diagnose Bannister model calculations
- `diagnose_tdf_stages.py` - Analyze TDF stage classifications for errors
- `compare_data_sources.py` - Compare different data sources for consistency
- `compare_db_vs_calc.py` - Compare database values vs. calculated values

## Fix/Repair Scripts
- `fix_tdf_classifications.py` - Correct TDF stage misclassifications
- `fix_lint_issues.py` - Automated linting fixes
- `fix_trailing_whitespace.py` - Clean up whitespace issues
- `add_missing_stage2.py` - Recovery tool for missing TDF stages

## Data Management
- `manage_memory_db.py` - Database maintenance and cleanup
- `export_strava_for_testing.py` - Export Strava data for testing

## Testing
- `test_power_tss.py` - Test power and TSS calculations
- `test_tsb_parameters.py` - Test TSB parameter calculations

## Usage
These scripts are typically run manually for debugging or maintenance purposes. They are not part of the regular workflow automation.
