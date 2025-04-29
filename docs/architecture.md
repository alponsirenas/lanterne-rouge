# Architecture

## Current Architecture (v0.2.1–v0.3.0)

### Core Components

- **Tour Coach** (`run_tour_coach.py`):
  - Orchestrates daily update sequence.

- **MissionConfig** (`mission_config.py`):
  - Loads structured simulation goals and constraints.

- **Observation Layer** (`monitor.py`):
  - Gathers data from Oura and Strava APIs.
  - Structures daily observations.

- **Reasoning Module** (`reasoner.py`):
  - Analyzes observations and recommends daily action.
  - Aligned with MissionConfig.

- **Output Layer**:
  - Saves reports and logs into `/output/`.

- **(GUI Incoming)**:
  - Gradio dashboard to present daily results.

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
  - Prepares human-readable outputs and GUI updates.

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

