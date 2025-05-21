# Architecture

## Current Architecture (v0.3.0‑dev)

### Core Components

- **Tour Coach** (`run_tour_coach.py`):
  - Orchestrates daily update sequence. It also triggers notification delivery through the new `notify.py` layer.
  - `tour_coach.run()` accepts an optional `MissionConfig`. If omitted, the config is loaded from `missions/tdf_sim_2025.toml` by default.
  - Includes subprocess calls for expanded Oura contributor tracking, secure GitHub secret updates using PAT with appropriate headers, and readiness/fitness metrics logging before generating the daily output.
    - Pushes updated logs and database snapshots to GitHub (GitHub‑Actions step, currently blocked by permissions ‑ see Next Steps).

- **MissionConfig** (`mission_config.py`):
  - Loads structured simulation goals and constraints from TOML (`missions/*.toml`).
  - Supports runtime overrides from environment secrets (e.g. `STRAVA_CLIENT_ID`).
  - Persists the active config into SQLite (`lanterne.db`) via `cache_to_sqlite()` for reproducibility.

- **Observation Layer** (`monitor.py`):
  - Gathers data from Oura and Strava APIs.
  - Structures daily observations including full readiness contributor fields.
  - Handles missing values gracefully.

- **Reasoning Module** (`reasoner.py`):
  - Analyzes observations and recommends daily action.
  - Aligned with MissionConfig.

- **Workout Plan Generator** (`plan_generator.py`):
  - Uses OpenAI via `ai_clients.py` to create a daily workout plan.

- **Peloton Matcher** (`peloton_matcher.py`):
  - Suggests a matching Peloton class for the generated workout type.

- **Memory Layer** (`memory_bus.py`):
  - Stores observations, decisions, and reflections in `memory/lanterne.db`.
  - Provides recent context for LLM prompts.

- **Output Layer**:
  - Saves reports and logs into `/output/`.

- **Notification Layer** (`notify.py`):
  - Sends e‑mail summaries (SMTP + Gmail App Password).
  - Sends SMS via carrier email gateway, with optional Twilio switch controlled by `USE_TWILIO`.

- **GUI (Streamlit)** (`app.py`):
  - Streamlit app using *st‑pages* to present daily results, charts, and mission status.
  - Chosen for faster iterative “generative‑UI” experiments versus the earlier Gradio mock‑up.

### GitHub Integration Layer

- **update_github_secret.py**:
  - Uses the GitHub API to programmatically update repository secrets.
  - Requires a Personal Access Token (PAT) with `repo` and `actions` scopes.
  - Now explicitly includes both `Authorization` and `User-Agent` headers in API requests. The workflow now attempts to commit updated `/output/` artifacts and `lanterne.db` back to the repo; this requires the PAT to have `contents:write` (or use a deploy key) — currently blocked by 403 errors.

### Next Steps toward v0.3.0 Release

- **Resolve GitHub Push**  
  Grant write access (PAT or Deploy Key) or switch to `actions/upload-artifact` for daily logs and database snapshots.

- **Finalize Streamlit Dashboard**  
  Connect the Communication layer to Streamlit; prototype generative‑UI patterns inspired by NN Group guidelines.

- **Harden Secrets Handling**  
  Remove `athlete_id` from MissionConfig; rely exclusively on repository/environment secrets.

- **Expand Test Coverage**  
  Pytest for MissionConfig SQLite caching, Oura readiness contributors, and notification fallbacks.

- **Decide MissionConfig Storage Long‑term**  
  Evaluate keeping TOML + SQLite vs. full Postgres for multi‑athlete scaling.

### Data Flow
```markdown
MissionConfig
    ↓
Daily Observations → Reasoning → Decision + Log → GUI
```



## Future Architecture (v0.4.0+ and Beyond)

### Modular Multi-Agent System

- **Mission Agent**:
  - Owns mission goals, timelines, critical stages.

- **Observation Agent**:
  - Pulls and preprocesses external fitness and readiness data.

- **Reasoning Agent**:
  - Decides daily adaptations based on observations and mission.

- **Planning Agent**:
  - Updates long-term and micro-training plans dynamically.

- **Communication Agent**:
  - Prepares human-readable outputs and drives the Streamlit (or successor generative‑UI) front-end.

- **Reflection Agent** (future):
  - Evaluates and adapts reasoning strategies over time.

### Future Data Flow

```markdown
Mission Agent
    ↓
Observation Agent → Reasoning Agent ↔ Reflection Agent
    ↓
Planning Agent
    ↓
Communication Agent → GUI / Reports
```

### Future Goals

- **Self-Correcting Planning**:
    - Dynamically adjust plans based on emerging readiness trends.

- **Agent-to-Agent Negotiation**:
    - Enable agents to resolve conflicts (e.g., Mission Agent overriding Reasoning Agent to prioritize critical goals).

- **Reflection-Driven Adaptation**:
    - Incorporate learning from past training blocks to improve future strategies.

