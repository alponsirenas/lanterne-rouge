# AI Integration - Enhanced Agent-Based System

## Overview

| Area       | Details                                                                 |
|------------|-------------------------------------------------------------------------|
| **Purpose** | Intelligent agent-based training recommendations with LLM reasoning   |
| **LLM Role** | Primary decision-maker and communicator (with rule-based fallback)    |
| **Input**   | Live biometric data, training history, mission goals, training phase  |
| **Output**  | Personal, contextual training decisions with detailed explanations     |
| **Timing**  | Daily automated runs with real-time data integration                   |
| **Model**   | GPT-4-turbo-preview (default), configurable                          |
| **Architecture** | Agent-based: ReasoningAgent, WorkoutPlanner, CommunicationAgent   |ntegration Plan for Lanterne Rouge

## Overview

| Area       | Details                                                                 |
|------------|-------------------------------------------------------------------------|
| **Purpose** | Help the Reasoning Module generate natural language coaching summaries based on the agent’s decision and context. |
| **LLM Role** | Advisor/Communicator, not decision-maker yet.                         |
| **Input**   | Structured observations, decision outputs, mission goals.             |
| **Output**  | Short, human-readable summary explaining why today’s action was chosen. |
| **Timing**  | Happens after the Reasoning Module decides on action (push, ease, recover, etc.). |
| **Model**   | Use OpenAI’s GPT-4 or GPT-3.5-turbo (small prompts, low cost).         |
| **Invocation** | Single short prompt per day during the agent’s daily run.          |


## Technical Design

### Steps

1. **Reasoning Module makes today’s decision.**
   Example: “Ease off today because TSB is -27 and readiness dropped to 58.”
2. **System builds a compact prompt:**
   Example:
   `"Explain today’s training recommendation based on readiness=58, TSB=-27, Mission target=Tour Simulation stage preservation."`
3. **Call the LLM with the prompt.**
4. **Capture the generated explanation and:**
   - Save it into `output/reasoning_log.csv`.
   - Display it in the GUI dashboard.

> **Note:** The LLM provides the narrative voice of the agent without altering decisions.



## Example Prompt and Expected Output

### Prompt sent to LLM:

You are an AI coach for endurance athletes. Today's observation: readiness=58 (moderate), TSB=-27 (high fatigue). The athlete's mission is to complete a Tour de France simulation with cumulative stage efforts. Today's agent decision is to insert a recovery day. Write a short explanation (~2 sentences) of the decision for the athlete.

### Expected Output:

Based on your current recovery state, today’s focus will be active recovery. Your fatigue levels are high, and preserving your long-term ability to handle stage simulations is the priority.


## Implementation Scope

| File                                   | Action                                        |
|----------------------------------------|-----------------------------------------------|
| `lanterne_rouge/reasoner.py`          | After decision, prepare short LLM prompt.     |
| `lanterne_rouge/llm_explainer.py`     | Create small module to manage LLM API call.   |
| `output/reasoning_log.csv`             | Add explanation field.                         |
| GUI                                    | Display today’s decision and explanation together. |


## Minimal LLM API Integration Needs

| Need                        | Details                                                  |
|-----------------------------|----------------------------------------------------------|
| OpenAI API Key              | Add to .env: `OPENAI_API_KEY=...`                        |
| Small safe timeout (e.g., 10 sec max) | In case LLM delays                                   |
| 100 tokens max per call     | Control cost (fractions of a cent/day)                   |


## Infrastructure Needed for AI Agent Growth in Lanterne Rouge

| Layer                        | Requirements                                                                 | Why It Matters                                                             |
|------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------|
| Secrets and Credentials Management | Secure .env management for API keys (OpenAI, future APIs). Optional vault integration later. | Protect sensitive credentials, avoid leaking keys.                        |
| Memory / State Management     | Light structured memory system: JSON or lightweight database (SQLite) for storing past observations, reasoning outputs, mission state snapshots. | Enables Reflection Agent, trend learning, longitudinal reasoning.          |
| Agent Communication Layer     | Standard data structure (e.g., JSON-like dicts) for input/output between agents. Possibly a shared memory_bus module. | Modular, pluggable agents. Easier AI component swaps later.               |
| AI Model Management           | Small module to manage API clients (OpenAI, HuggingFace Inference API, etc.) centrally. Control timeouts, token usage, retries. | Centralized safety, cost control, fallback handling.                      |
| Sandboxing and Testing Pipelines | Separate offline test runs for new agent behaviors. Simulate fake observation histories to verify reasoning outputs. | Test new AI reasoning safely before pushing to production flow.            |
| Versioning of AI Components   | Simple system to track active model or prompt versions inside outputs/logs. | Reproducibility, debugging, safe rollback if reasoning goes wrong.        |
| Monitoring and Cost Control   | Track API usage (token counts, calls/day) optionally log costs. Simple daily reporting. | Prevent runaway API costs, optimize call efficiency.                      |
| Scaling Infrastructure (later)| Optional lightweight cloud hosting (if you want Lanterne Rouge to operate continuously). Could use serverless like AWS Lambda or small VPS. | Only needed if user base grows or you want agent automation (daily runs without manual launch). |



## Minimum Stack for Near-Term Growth

| Component                    | What You Can Use Now                                                                 |
|------------------------------|-------------------------------------------------------------------------------------|
| Secrets                       | .env + Python’s dotenv (what you already have)                                      |
| Memory                        | JSON logs (extend reasoning_log, readiness_log) initially, SQLite later              |
| Agent Communication           | Shared data model classes (e.g., Observation, Decision, MissionStatus)               |
| AI Management                 | Tiny ai_clients.py module wrapping OpenAI, Huggingface API calls                     |
| Sandbox Testing               | Simple tests/agent_scenarios/ directory with pre-recorded observation simulations     |
| Version Tracking              | Add model version + prompt ID into daily logs                                        |
| Monitoring                    | Simple daily API usage summary printed to console or saved                           |


## Sketch of Folder Layout as AI Integration Grows

```
lanterne-rouge/
├── src/
│   └── lanterne_rouge/
│       ├── agents/
│       │   ├── mission_agent.py
│       │   ├── observation_agent.py
│       │   ├── reasoning_agent.py
│       │   ├── planning_agent.py
│       │   └── communication_agent.py
│       ├── memory/
│       │   ├── memory_bus.py
│       │   └── state_store.py
│       ├── ai/
│       │   ├── ai_clients.py
│       │   ├── prompts/
│       │   │   ├── reasoning_prompts.json
│       │   │   └── communication_prompts.json
│       └── utils/
│           ├── config_loader.py
│           └── logger.py
├── tests/
│   ├── agent_scenarios/
│   └── unit/
├── config/
├── output/
├── docs/
│   └── architecture.md
├── run_tour_coach.py
```


## Scope for Lanterne Rouge Daily Agent Automation

| Component                    | Assumption                                   |
|------------------------------|----------------------------------------------|
| Daily Run Frequency           | 1 time per day                              |
| Data Sources                  | Oura API, Strava API (both free for personal use) |
| Reasoning Module              | LLM-assisted lightweight reasoning text generation |
| Communication                 | Streamlit dashboard or simple output logging |
| Hosting                       | Tiny server (VPS or serverless)              |


## Cost Breakdown

| Category                      | Estimate (Monthly) | Notes                                                                 |
|-------------------------------|--------------------|-----------------------------------------------------------------------|
| LLM Usage (OpenAI)            | $1–3               | Based on one GPT-3.5-turbo call per day (~300–500 tokens), 30 days/month |
| Cloud Hosting                 | $5–7               | Tiny VPS (like DigitalOcean “Basic” droplet, ~1GB RAM) or AWS Lightsail |
| Storage                       | $0 (initially)     | Tiny logs only, can stay on server for now.                          |
| Monitoring / Alerts           | $0–2 (optional)    | Free basic uptime monitors, cheap alerting services.                  |
| Domain (optional)            | $0–10/year         | Only if you want a custom dashboard address (not needed initially).   |


### Estimated Total:

~$6–10/month for a fully autonomous, live Lanterne Rouge agent system.



## LLM Costs in Detail

| Model                        | Cost per 1K tokens   | Daily Token Estimate | Monthly Cost Estimate         |
|------------------------------|-----------------------|----------------------|--------------------------------|
| GPT-3.5-turbo                | ~$0.0015 per 1K tokens| ~500 tokens/day      | ~$0.0225/day → ~$0.70/month    |
| GPT-4 (if needed later)      | ~$0.03–0.06 per 1K tokens | (same usage)        | ~$2–4/month                    |



## Automation Setup Plan

| Step                          | Tool                                         |
|-------------------------------|----------------------------------------------|
| Daily Scheduling               | Linux cron job or simple Cloud Scheduler (free/cheap) |
| Hosting                        | Tiny VPS (DigitalOcean $5, AWS Lightsail $3.50–5) |
| Agent Execution                | Run python run_tour_coach.py daily automatically |
| Failure Handling               | Basic logging + retry if internet/API error  |
| Output Delivery                | Save local outputs, optional email/telegram alert with summary |



### Stretch Goals Later (Optional Extra Cost)

| Stretch                                | Cost                                      |
|----------------------------------------|-------------------------------------------|
| Push results to a private dashboard or mobile app | Small API hosting costs ($2–5/month extra) |
| Automate GitHub backup of agent logs (versioned) | Free if using Actions, pennies if S3-style hosting |
| Multi-user scaling (coaching more athletes)      | Would need $10–20 server, not now          |


## Current Implementation Status

✅ **COMPLETED**: Full agent-based system with LLM reasoning as default  
✅ **COMPLETED**: First-person, conversational communication  
✅ **COMPLETED**: Real-world integration (Oura + Strava APIs)  
✅ **COMPLETED**: Structured output format with time-in-zones  
✅ **COMPLETED**: Graceful fallback to rule-based reasoning  
✅ **COMPLETED**: Production-ready error handling  

## Agent Architecture

### ReasoningAgent (`reasoner.py`)
**Purpose**: Makes intelligent training decisions based on athlete metrics

**LLM Integration**:
- **Model**: GPT-4-turbo-preview (configurable via `OPENAI_MODEL`)
- **Mode**: JSON-structured responses for consistent parsing
- **Context**: Training phase, goal proximity, recent training history
- **Tone**: First-person, encouraging, plain language
- **Fallback**: Automatic switch to rule-based if LLM fails

**Input Processing**:
```python
{
  "readiness_score": 76,
  "ctl": 35.6,
  "atl": 45.2, 
  "tsb": -9.6,
  "training_phase": "Taper",
  "days_to_goal": 5
}
```

**Output Structure**:
```python
TrainingDecision(
  action="ease",
  reason="Given your current metrics and the fact that you're in the taper phase...",
  intensity_recommendation="low",
  flags=["negative_tsb"],
  confidence=0.8
)
```

### WorkoutPlanner (`plan_generator.py`)
**Purpose**: Generates structured workout plans based on training decisions

**Features**:
- Phase-aware workout selection (Base, Build, Peak, Taper)
- Time-in-zone prescriptions
- Load estimation for training stress management
- Structured WorkoutPlan objects

### CommunicationAgent (`ai_clients.py`)
**Purpose**: Creates empathetic, natural language summaries

**Output Sections**:
1. Training phase context with goal countdowns
2. Current fitness metrics display
3. Detailed reasoning explanation
4. Structured workout plan

### TourCoach (`tour_coach.py`)
**Purpose**: Orchestrates all agents for coherent daily recommendations

**Integration**:
- Coordinates agent workflow
- Manages memory logging
- Handles output generation
- Provides configuration flexibility

## Technical Implementation

### LLM Prompt Engineering

**System Prompt**:
```
You are an expert cycling coach AI speaking directly to your athlete. 
Analyze their metrics and training context to make a structured training decision.

Guidelines:
- Address the athlete directly using "you" and "your"
- Use plain, conversational language
- Be encouraging and supportive
- Explain WHY this decision helps them reach their goals
```

**Response Format**:
```json
{
  "action": "recover|ease|maintain|push",
  "reason": "detailed first-person explanation",
  "intensity_recommendation": "low|moderate|high",
  "flags": ["contextual_flags"],
  "confidence": 0.8
}
```

### Configuration Management

**Environment Variables**:
```bash
# Reasoning mode (default: LLM)
USE_LLM_REASONING=true

# OpenAI configuration
OPENAI_API_KEY=required_for_llm_mode
OPENAI_MODEL=gpt-4-turbo-preview

# Data sources
OURA_ACCESS_TOKEN=live_biometric_data
STRAVA_REFRESH_TOKEN=training_history
```

### Error Handling

**Graceful Degradation**:
1. LLM failure → automatic rule-based fallback
2. API unavailable → cached/mock data
3. JSON parsing error → rule-based decision
4. Network issues → offline operation

## Real-World Integration

### Data Sources
- **Oura Ring**: Live readiness scores, HRV, sleep data
- **Strava**: Training history, CTL/ATL/TSB calculations
- **Mission Config**: Training phases, goal dates, constraints

### Output Quality
**Before (Rule-based)**:
- "Metrics indicate steady training state" (7 words)

**After (LLM-enhanced)**:
- "Given your current metrics and the fact that you're in the taper phase with your goal event just 5 days away, it's crucial to fine-tune your condition without overdoing it..." (150+ words)

### Performance Metrics
- **LLM Response Time**: ~2-3 seconds
- **Fallback Success Rate**: 100% (rule-based always available)
- **API Integration**: Live data from Oura/Strava
- **Output Consistency**: Structured format maintained across modes

## Usage Examples

### Daily Automated Run
```bash
# Default LLM mode
python -c "from src.lanterne_rouge.tour_coach import run_tour_coach; run_tour_coach()"

# Force rule-based mode  
USE_LLM_REASONING=false python scripts/daily_run.py
```

### Programmatic Usage
```python
from lanterne_rouge.tour_coach import TourCoach
from lanterne_rouge.mission_config import bootstrap

config = bootstrap("missions/tdf_sim_2025.toml")

# LLM-based coach (default)
coach = TourCoach(config)

# Rule-based coach
coach = TourCoach(config, use_llm_reasoning=False)

# Generate recommendation
summary = coach.generate_daily_recommendation(metrics)
```

## Benefits Achieved

1. **Intelligent Reasoning**: Context-aware decisions considering training phase and goals
2. **Personal Communication**: First-person, encouraging tone builds athlete engagement  
3. **Production Reliability**: Graceful fallbacks ensure system always produces output
4. **Real-world Integration**: Live data from actual biometric and training sources
5. **Structured Output**: Consistent format enables automation and integration
6. **Flexible Configuration**: Easy switching between reasoning modes

## Future Enhancements

- **Multi-athlete Support**: Extend for coaching multiple athletes
- **Learning Integration**: Incorporate outcome feedback for decision refinement  
- **Advanced Periodization**: Season-long training plan optimization
- **Wellness Integration**: Expanded biometric data sources
- **Mobile Interface**: Native app for athlete interaction

## Historical Context

### Previous Implementation
The original plan was for LLM integration as a post-processing step to explain rule-based decisions. The system has evolved far beyond this to use LLM as the primary reasoning engine.

### Evolution Timeline
1. **v0.1**: Rule-based decisions only
2. **v0.2**: LLM explanations of rule-based decisions  
3. **v0.3**: Full agent-based architecture with LLM primary reasoning
4. **Current**: Production-ready system with real-world integration

The enhanced system represents a complete transformation from basic rule-based logic to sophisticated AI-powered coaching that provides personalized, contextual, and engaging training recommendations.
