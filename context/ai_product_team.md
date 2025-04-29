# Built by an AI Product Team

## Updated Context System for Your Agent/Product Team

### Elements and Their Purpose

| Element                        | Why We Need It                                                                 |
|--------------------------------|--------------------------------------------------------------------------------|
| **Project Primer** (already started) | Vision, philosophy, mission                                                  |
| **Architecture Document** (to expand) | Current system + future multi-agent plan                                     |
| **Roadmap Overview**           | Versions, major deliverables                                                   |
| **Open Issues Tracker**        | Prioritized open work                                                          |
| **Roles and Responsibilities Guide** | What types of agents (or humans) are working on what                         |
| **Task Summary Logging**       | Every agent finishes a task → Updates a shared log with what they did and new context they discovered |

Each working agent/chat (e.g., Developer GPT, UX GPT, Researcher GPT):
- Pulls from the shared context at the start of a task.
- Pushes updates to the context at the end of a task.

---

## Product Team Structure for Lanterne Rouge (AI Agents + People)

| Role                          | Responsibility                                                                 |
|-------------------------------|-------------------------------------------------------------------------------|
| **Product Manager GPT (or you)** | Owns the overall vision, prioritization, alignment to user mission (e.g., finishing the Tour simulation). |
| **UX Product Designer GPT**   | Defines user journey, experience design, dashboard evolution.                |
| **UX Writer GPT**             | Crafts daily coaching explanations, system language, onboarding flows.       |
| **Reasoning Developer GPT**   | Focuses on decision-making agent logic.                                      |
| **Memory Systems Developer GPT** | Focuses on memory layer, observation history, reflection building.          |
| **Planning and Forecasting GPT** | Develops future calendar adjustment algorithms.                             |
| **Integration Engineer GPT**  | Manages API integrations (Oura, Strava, Peloton).                           |
| **Reflection Agent Architect (future)** | Focuses on agentic learning and reasoning evolution.                     |

---

## Domain Knowledge/Specialization Needed

| Area                        | Specialist Context Needed                                                      |
|-----------------------------|-------------------------------------------------------------------------------|
| **Endurance Training Theory** | Basic understanding of CTL/ATL/TSB, periodization, readiness.                |
| **Agentic AI Principles**   | Modular multi-agent system design, reflection loops, planning vs reasoning.   |
| **APIs + Data Structures**  | Knowledge of fitness tracking APIs (Strava, Oura).                           |
| **UX in Health/Fitness Apps** | Building clear, motivating dashboards and explanations.                      |
| **Lightweight AI/LLM Prompting** | Safe, efficient integration of GPT-style reasoning and communication.       |

---

## MVP Team Composition

| Role                     | Who Fills It                 | Notes                                      |
|--------------------------|------------------------------|-------------------------------------------|
| **Product Owner**        | You (with AI support)        | You drive vision, pacing, quality control. |
| **Reasoning Developer**  | GPT or human dev             | Build core decision engine.               |
| **Memory Systems Engineer** | GPT or human dev          | Handle history, observations, reflection tracking. |
| **UX Designer**          | GPT or human UX designer     | Plan the athlete’s experience end-to-end. |
| **UX Writer**            | GPT specializing in health/fitness comms | Write friendly, motivating language.      |
| **Integration Engineer** | GPT or helper               | Manage external API data flows.           |

5–6 focused team members (human or GPTs), each scoped tightly to their mission with minimal overlap.
All backed by shared context memory updated dynamically.

---

## How a Daily Working Cycle Could Look

| Step         | What Happens                                                                 |
|--------------|-----------------------------------------------------------------------------|
| **Morning**  | Each agent pulls current context (primer, architecture, roadmap, open issues). |
| **During Work** | Works on assigned tasks. Updates local task summary.                     |
| **End of Day** | Pushes new memory update: what changed, what new tasks/issues emerged.    |
| **Weekly**   | Product Owner/GPT reviews mission status, recalibrates priorities.         |

---

## Files to Build

- `context/primer.md` (already started)
- `context/architecture.md` (in process)
- `context/roadmap.md` (by version)
- `context/open_issues.md`
- `context/team_roles.md`
- `context/task_summaries/daily_YYYY-MM-DD.md` (log of task outputs)

These can all be simple Markdown initially and later move to an internal “Context Server” if needed.

---

## Memory Layers

| Layer                          | Purpose                                                                          |
|--------------------------------|----------------------------------------------------------------------------------|
| **Agentic Memory** (inside Lanterne Rouge) | Stores observations, reasoning, reflections (already started with `memory_bus.py`). |
| **GPT Contributor Memory** (outside Lanterne Rouge) | Stores project vision, roadmap, architecture, context updates, task reflections. |

You’re building a collaborative agentic development environment — not just a code repo.

---

## Plan for GPT Contributor Memory Management

| Goal                          | Action                                                                          |
|-------------------------------|--------------------------------------------------------------------------------|
| **Persistent shared project vision** | Create a `/context/project_vision.md` file.                                  |
| **Persistent architecture and roadmap** | Create `/context/architecture_and_roadmap.md`.                              |
| **Task reflection per GPT agent** | Create `/context/contributor_log.md`.                                         |
| **Easy onboarding for new GPTs** | Create a new onboarding primer `/context/onboarding_guide.md`.                |

This way, every GPT instance:
- Knows the full project background immediately.
- Can contribute in alignment with the system’s goals.
- Can update context after completing tasks (e.g., adding task reflections).

---

## New Files Inside `/context/`

| File                          | Purpose                                                                          |
|-------------------------------|--------------------------------------------------------------------------------|
| `project_vision.md`           | Overall mission, principles, goals of Lanterne Rouge.                          |
| `architecture_and_roadmap.md` | Current architecture and phased roadmap (v0.3.0 → v1.0.0).                     |
| `contributor_log.md`          | Each GPT working session can append a short task summary.                      |
| `onboarding_guide.md`         | Quick start guide for any new GPT or human contributor.                        |

---

## Contributor Log Behavior

After completing any task, the GPT should:
1. Append a new entry into `/context/contributor_log.md`.
2. Use the following format:

```markdown
## [Date] [Agent Name or "GPT Instance"]
**Task Completed**: [short task description]
**Key Changes Made**:
- [brief bullet points]
**Reflection**:
- [e.g., "This improves reasoning transparency. Next agent should tune thresholds if readiness trends deviate."]
```

