# Lanterne Rouge — Project Context Primer

**Primer Version:** 0.3.0‑dev

## Purpose

Build an agentic AI system that adapts endurance training dynamically based on real-world data and mission-driven event goals. Inspired by the spirit of finishing strong, not just winning.

## Core Architecture

- MissionConfig: Defines event goals, fitness targets, stage demands.
- Observation Layer: Collects daily readiness, fitness metrics.
- Reasoning Module: Decides daily actions based on observations and mission alignment.
- Planning Module: Updates training calendar dynamically.
- Communication Layer: Presents updates via Streamlit UI (Gradio prototype retired).
- Storage Layer: Persists mission configs, readiness logs, and plan state to SQLite (`memory/lanterne.db`).
- Reflection Layer (future): Learns from past decision outcomes.
- GitHub Integration Layer: Manages repository secrets programmatically via secure API calls

## Design Principles

- Mission-Locked Reasoning
- Safety First
- Transparency of decisions
- Modularity and Scalability
- Human-editable Configuration
- Lightweight at first, expandable later
- Generative UI‑ready (prepare components for future LL‑driven layouts)

## Current Roadmap

- Release v0.3.0‑dev — Mission‑Aware Daily Coaching  
    • MissionConfig v1.1 (TOML, runtime secret injection)  
    • Reasoning Module v1.0 (stable)  
    • Streamlit UI v0.1.0 for daily summaries & charts  
    • Full Oura contributor logging (completed)  
    • Secure GitHub secret rotation via `GH_PAT` (completed)  
    • Persist outputs to `memory/lanterne.db` and push to repo nightly

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
    ai_clients.py
    memory_bus.py
/config/             # templates or examples of MissionConfig files
    mission_config.toml   # example or template MissionConfig file
/missions/
    *.toml          # individual MissionConfig files
/scripts/
    run_tour_coach.py
    daily_run.py
    notify.py
    update_github_secret.py
/output/
    tour_coach_update.txt
    readiness_score_log.csv
    reasoning_log.csv
    memory/lanterne.db
```

---

## Agent Roles

| Agent Name          | Responsibility                                                                 | Related Modules                      |
|---------------------|----------------------------------------------------------------------------------|--------------------------------------|
| Tour Coach Agent    | Summarizes daily readiness, generates training recommendations                  | `tour_coach.py`, `scripts/run_tour_coach.py`, `daily_run.py` |
| Reasoning Agent     | Aligns observations with MissionConfig to make actionable decisions              | `reasoner.py`, `plan_generator.py`, `ai_clients.py` |
| GitHubOps Agent     | Updates secrets and interacts with GitHub programmatically                      | `scripts/update_github_secret.py`   |
| Monitor Agent       | Pulls Oura and Strava data, calculates readiness and fitness baselines           | `monitor.py`, `strava_api.py`       |
| UI Agent (Streamlit) | Renders daily summaries and charts for humans | `scripts/run_tour_coach.py` |

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
- REPO_PUSH_PAT — scoped PAT that allows GitHub Actions to commit artifacts

---

## Readiness Score Log Schema

The file `output/readiness_score_log.csv` contains:

- `timestamp`, `score`
- Contributors: `activity_balance`, `body_temperature`, `hrv_balance`, `previous_day_activity`, `previous_night`, `recovery_index`, `resting_heart_rate`, `sleep_balance`
- Contributor values may be missing (e.g. `null`) — system handles gracefully.

---

## Component Versions

| Component            | Current Version | Notes                                    |
|----------------------|-----------------|-------------------------------------------|
| Tour Coach Agent     | v0.3.0‑dev      | Mission‑aware daily training updates      |
| Reasoning Module     | v1.0            | Mission‑aligned decision making           |
| Streamlit UI         | v0.1.0          | First interactive dashboard               |
| GitHubOps Agent      | v0.1.1          | Secure repo secret rotation + push rights |
| Oura Contributor Log | v1.0            | Full contributor set recorded             |
