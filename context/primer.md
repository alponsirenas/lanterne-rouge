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
- GitHub Integration Layer: Manages repository secrets programmatically via secure API calls

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
- Expanded Oura contributor tracking with multiple readiness factors now logged per day
- Integrated secure GitHub secret update mechanism using `GH_PAT` and custom headers in `update_github_secret.py`

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
    update_github_secret.py
    daily_run.py
/config/
    mission_config.json
/output/
    tour_coach_update.txt
    readiness_score_log.csv
    reasoning_log.csv
/scripts/
    update_github_secret.py
    daily_run.py
```

---

## Agent Roles

| Agent Name          | Responsibility                                                                 | Related Modules                      |
|---------------------|----------------------------------------------------------------------------------|--------------------------------------|
| Tour Coach Agent    | Summarizes daily readiness, generates training recommendations                  | `tour_coach.py`, `daily_run.py`     |
| Reasoning Agent     | Aligns observations with MissionConfig to make actionable decisions              | `reasoner.py`, `plan_generator.py`  |
| GitHubOps Agent     | Updates secrets and interacts with GitHub programmatically                      | `update_github_secret.py`           |
| Monitor Agent       | Pulls Oura and Strava data, calculates readiness and fitness baselines           | `monitor.py`, `strava_api.py`       |

---

## Daily Execution Flow

1. `daily_run.py` is the main entry point.
2. Oura data is pulled and readiness contributors logged via `monitor.py`.
3. Strava data is fetched to update CTL, ATL, TSB scores.
4. `record_readiness_contributors()` stores daily readiness and contributors in `readiness_score_log.csv`.
5. `reasoner.py` evaluates readiness against MissionConfig to generate or adapt the plan.
6. Tour Coach Agent writes the daily update to `tour_coach_update.txt`.
7. `update_github_secret.py` optionally updates secrets for future automation.

---

## Environment & Secrets

These must be defined in the GitHub repository or local `.env` file:

- `EMAIL_ADDRESS`, `EMAIL_PASS`, `TO_EMAIL`, `TO_PHONE`
- `OURA_TOKEN`
- `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REFRESH_TOKEN`
- `GH_PAT` — used with `Authorization: token` header
- `REPO_OWNER`, `REPO_NAME` — used for GitHub API requests

---

## Readiness Score Log Schema

The file `output/readiness_score_log.csv` contains:

- `timestamp`, `score`
- Contributors: `activity_balance`, `body_temperature`, `hrv_balance`, `previous_day_activity`, `previous_night`, `recovery_index`, `resting_heart_rate`, `sleep_balance`
- Contributor values may be missing (e.g. `null`) — system handles gracefully.

---

## Component Versions

| Component            | Current Version | Notes                                |
|----------------------|-----------------|--------------------------------------|
| Tour Coach Agent     | v0.2.1          | Daily readiness and training updates |
| Reasoning Module     | v1.0            | Mission-aligned decision making      |
| GitHubOps Agent      | v0.1.0          | Secure repo secret updates           |
| Oura Contributor Log | v1.0            | Full contributor set now recorded    |