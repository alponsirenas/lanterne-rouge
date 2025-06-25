# Bannister Model Implementation

## Overview

The Bannister model, also known as the impulse-response model, is used to quantify training stress and calculate fitness (CTL), fatigue (ATL), and form (TSB) metrics. This document explains how Lanterne Rouge implements the model to match intervals.icu calculations.

## Key Metrics

- **CTL (Chronic Training Load)**: A measure of fitness, representing the long-term training load. Uses a 42-day time constant.
- **ATL (Acute Training Load)**: A measure of fatigue, representing the short-term training load. Uses a 7-day time constant.
- **TSB (Training Stress Balance)**: A measure of form/freshness, calculated as CTL - ATL.

## Implementation Details

The Bannister model is implemented in `src/lanterne_rouge/monitor.py` with the following key features:

### Time Constants

```python
CTL_TC = 42  # days
ATL_TC = 7   # days
K_CTL = 1 - math.exp(-1 / CTL_TC)
K_ATL = 1 - math.exp(-1 / ATL_TC)
```

### Data Sources

Training stress scores are collected from:

1. Primary source: `icu_training_load` values from Strava activities
2. Fallback: `relative_effort` or `suffer_score` values from Strava activities

### Calculation Method

The model uses exponential decay to calculate CTL and ATL:

```python
# For each day's training load (tss)
ctl = ctl * (1 - K_CTL) + tss * K_CTL
atl = atl * (1 - K_ATL) + tss * K_ATL
```

This formula is mathematically equivalent to `value += K * (tss - value)` but produces values that better match intervals.icu's implementation.

### Lookback Period

The model uses a 90-day lookback period to allow for accurate CTL calculation, since CTL has a 42-day time constant.

## Testing 

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
