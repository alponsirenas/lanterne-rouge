# Architecture

## Current Architecture (v0.3.1) - Enhanced Agent-Based System

### Agent-Based Design

The Lanterne Rouge system has been refactored into a modern agent-based architecture with intelligent reasoning capabilities:

#### Core Agents

- **ReasoningAgent** (`reasoner.py`):
  - **Dual-mode reasoning**: LLM-based (default) and rule-based fallback
  - **Structured output**: TrainingDecision with action, reasoning, intensity, flags, and confidence
  - **First-person communication**: Speaks directly to athlete using plain language
  - **Contextual analysis**: Considers training phase, TSB, readiness, and goal proximity
  - **Graceful fallback**: Automatically switches to rule-based if LLM unavailable

- **WorkoutPlanner** (`plan_generator.py`):
  - **Phase-aware planning**: Adapts workouts based on training phase (Base, Build, Peak, Taper)
  - **Structured output**: WorkoutPlan with type, description, duration, zones, and load
  - **Time-in-zone prescriptions**: Detailed zone breakdowns for structured training
  - **Load estimation**: Calculates expected training stress for each workout

- **CommunicationAgent** (`ai_clients.py`):
  - **Empathetic summaries**: Natural language training summaries
  - **Multi-section output**: Phase context, metrics, reasoning, and workout details
  - **Goal tracking**: Days to next phase and goal countdowns
  - **Coach-like personality**: Encouraging, supportive tone

- **TourCoach** (`tour_coach.py`):
  - **Agent orchestration**: Coordinates ReasoningAgent, WorkoutPlanner, and CommunicationAgent
  - **Configurable reasoning**: Supports both LLM and rule-based modes
  - **Memory integration**: Logs observations, decisions, and reflections
  - **Output generation**: Produces structured daily training summaries

### Reasoning Modes

#### LLM-Based Reasoning (Default)
- **Model**: GPT-4-turbo-preview (configurable)
- **Context**: Training phase, goal proximity, recent training history
- **Output**: Detailed 150+ word explanations with scientific rationale
- **Tone**: First-person, conversational, encouraging
- **Configuration**: `USE_LLM_REASONING=true` (default)

#### Rule-Based Reasoning (Fallback)
- **Logic**: Threshold-based decisions using TSB, readiness, and CTL/ATL
- **Output**: Concise explanations based on specific metrics
- **Reliability**: Always available, no API dependencies
- **Use case**: Fallback when LLM unavailable or for deterministic decisions

### Core Components

- **Tour Coach** (`run_tour_coach.py`):
  - Orchestrates daily update sequence. It also triggers notification delivery through the new `notify.py` layer.
  - `tour_coach.run()` accepts an optional `MissionConfig`. If omitted, the config is loaded from `missions/tdf_sim_2025.toml` by default.
  - Includes subprocess calls for expanded Oura contributor tracking, secure GitHub secret updates using PAT with appropriate headers, and readiness/fitness metrics logging before generating the daily output.
    - Pushes updated logs and database snapshots to GitHub (GitHub‑Actions step, currently blocked by permissions ‑ see Next Steps).

- **MissionConfig** (`mission_config.py`):
  - Loads structured simulation goals and constraints from TOML (`missions/*.toml`).
  - Supports runtime overrides from environment secrets (e.g. `STRAVA_CLIENT_ID`).
  - Persists the active config into SQLite (`memory/lanterne.db`) via `cache_to_sqlite()` for reproducibility.

- **Observation Layer** (`monitor.py`):
  - Gathers data from Oura and Strava APIs.
  - Structures daily observations including full readiness contributor fields.
  - Handles missing values gracefully.

- **Reasoning Module** (`reasoner.py`):
  - Analyzes observations and recommends daily action.
  - Aligned with MissionConfig.

- **Workout Plan Generator** (`plan_generator.py`):
  - Uses OpenAI via `ai_clients.py` to create a daily workout plan.
  - Utilizes the new OpenAI client interface with appropriate model compatibility checks.
  - Supports JSON-formatted responses from compatible models (GPT-4-turbo, GPT-4o, etc.).

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
  - Now explicitly includes both `Authorization` and `User-Agent` headers in API requests. The workflow now attempts to commit updated `/output/` artifacts and `memory/lanterne.db` back to the repo; this requires the PAT to have `contents:write` (or use a deploy key) — currently blocked by 403 errors.

### Next Steps for Future Releases

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

## Enhanced Agent-Based Architecture (Current Implementation)

### Agent System Overview

The system has been refactored to use a modern agent-based architecture that provides intelligent, contextual training recommendations:

### Core Agents

#### ReasoningAgent (`reasoner.py`)
- **Dual reasoning modes**: LLM-based (default) and rule-based fallback
- **Structured decisions**: Returns TrainingDecision objects with action, reasoning, intensity, flags, and confidence
- **First-person communication**: Addresses athlete directly using "you" and "your"
- **Plain language**: Avoids jargon, explains technical terms when necessary
- **Contextual analysis**: Considers training phase, goal proximity, TSB, readiness, and recent history
- **Graceful degradation**: Falls back to rule-based logic if LLM unavailable

**Configuration:**
```bash
# LLM reasoning (default)
USE_LLM_REASONING=true
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=your_key

# Rule-based fallback
USE_LLM_REASONING=false
```

#### WorkoutPlanner (`plan_generator.py`)
- **Phase-aware workouts**: Adapts plans based on current training phase
- **Structured output**: WorkoutPlan objects with type, description, duration, zones, and load
- **Time-in-zone prescriptions**: Detailed breakdown of time spent in each training zone
- **Load estimation**: Calculates expected training stress for workout planning

#### CommunicationAgent (`ai_clients.py`)
- **Multi-section summaries**: Phase context, current metrics, reasoning, and workout details
- **Empathetic tone**: Encouraging, supportive language
- **Goal tracking**: Days to next phase and goal event countdowns
- **Coach personality**: Natural, conversational communication style

#### TourCoach (`tour_coach.py`)
- **Agent orchestration**: Coordinates all agents for coherent output
- **Configurable reasoning**: Supports both LLM and rule-based modes
- **Memory integration**: Logs observations, decisions, and reflections
- **Output management**: Generates and saves daily training summaries

### Reasoning Comparison

| Aspect | LLM-Based | Rule-Based |
|--------|-----------|------------|
| **Speed** | ~2-3 seconds | Instant |
| **Context** | Training phase, history, goals | Metrics only |
| **Explanation** | 150+ words, detailed rationale | Concise, threshold-based |
| **Adaptability** | High, considers nuanced factors | Deterministic |
| **Reliability** | Requires API key | Always available |
| **Tone** | Personal, encouraging | Technical, factual |

### Output Format

All modes produce structured output with:
1. **Training Phase Context** - Current phase, days to next phase/goal
2. **Current Fitness Metrics** - Readiness, CTL, ATL, TSB
3. **Training Logic** - Decision, detailed reasoning, intensity recommendation
4. **Workout Plan** - Type, description, duration, load, time in zones

### Environment Configuration

```bash
# Reasoning mode (default: LLM)
USE_LLM_REASONING=true|false

# OpenAI settings (for LLM mode)
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Oura and Strava integration
OURA_ACCESS_TOKEN=your_token
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_secret
STRAVA_REFRESH_TOKEN=your_refresh_token
```

### Usage Examples

```python
# Default LLM-based reasoning
from lanterne_rouge.tour_coach import run_tour_coach
run_tour_coach()

# Explicit rule-based reasoning
run_tour_coach(use_llm_reasoning=False)

# Custom model
run_tour_coach(use_llm_reasoning=True, llm_model="gpt-4o")
```

### Benefits

1. **Intelligent by default**: LLM provides contextual, adaptive reasoning
2. **Reliable fallback**: Rule-based logic ensures system always works
3. **Personal communication**: First-person, encouraging tone
4. **Structured output**: Consistent format regardless of reasoning mode
5. **Production ready**: Handles errors gracefully, integrates with existing workflow
6. **Configurable**: Easy switching between modes based on requirements

This enhanced architecture maintains all existing functionality while adding sophisticated AI reasoning capabilities that make the coaching recommendations more personal, contextual, and engaging.

