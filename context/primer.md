

# Lanterne Rouge — Project Context Primer

## Purpose

Build an agentic AI system that adapts endurance training dynamically based on real-world data and mission-driven event goals. Inspired by the spirit of finishing strong, not just winning.

## Core Architecture

- MissionConfig: Defines event goals, fitness targets, stage demands.
- Observation Layer: Collects daily readiness, fitness metrics.
- Reasoning Module: Decides daily actions based on observations and mission alignment.
- Planning Module: Updates training calendar dynamically.
- Communication Layer: Presents updates via GUI.
- Reflection Layer (future): Learns from past decision outcomes.

## Design Principles

- Mission-Locked Reasoning
- Safety First
- Transparency of decisions
- Modularity and Scalability
- Human-editable Configuration
- Lightweight at first, expandable later

## Current Roadmap

- Implement MissionConfig v1.0
- Build Reasoning Module v1.0
- Integrate daily GUI with Gradio
- Expand Oura contributor tracking

## Repository Layout

```markdown
/src/lanterne_rouge/
    monitor.py
    mission_config.py
    plan_generator.py
    peloton_matcher.py
    reasoner.py
    strava_api.py
    tour_coach.py
/config/
    mission_config.json
/output/
    tour_coach_update.txt
    readiness_score_log.csv
    reasoning_log.csv
```