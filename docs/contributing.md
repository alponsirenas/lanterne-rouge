# Contributing to Lanterne Rouge

Thank you for your interest in contributing to Lanterne Rouge — an agentic AI system for endurance athletes.

Our mission is to build a modular, adaptive, and transparent training partner that helps athletes complete their own race — stage by stage, day by day.

---

## Getting Started

1. **Fork the repository** and clone your fork locally.
2. **Create a Python virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate

	3.	Install dependencies:

pip install -r requirements.txt



⸻

Contribution Areas

We welcome contributions in these focus areas:
	•	MissionConfig: Structured event design and mission goal modeling.
	•	Reasoning Agent: Daily decision logic based on observations and mission constraints.
	•	Planning Agent: Updating future training blocks based on trend forecasts.
	•	Reflection Agent: Learning from past outcomes and modifying strategies.
	•	Observation Layer: Structured data ingestion from Oura, Strava, and others.
	•	GUI: Visualizing daily insights and agent reflections.
	•	LLM/AI integrations: Prompt tuning, model evaluation, reasoning explanations.
	•	Docs: Simulation strategy, system architecture, user experience flow.
	•	Documentation Review: Reviewing and updating project documentation to ensure accuracy and clarity.

⸻

Project Structure
	•	src/lanterne_rouge/: All core modules (agents, reasoning, planning, etc.)
	•	config/: JSON-based mission configurations
	•	output/: Logs and reports
	•	docs/: Design documentation, architecture, strategy
	•	context/: System-wide memory primer and coordination files

⸻

Guidelines
	•	Modularity first: Each agent or function should be independent and testable.
	•	Explainability: All decisions must be traceable to observations and mission goals.
	•	Transparency: Document your reasoning — logs are part of the agent’s voice.
	•	Reflection-ready: Design agents so they can be evaluated by future reflection loops.
	•	Resource-aware: LLM and API usage should be minimal, efficient, and fail-safe.

⸻

Submitting a Contribution
	1.	Create a branch off main with a descriptive name (e.g., reasoning-v2-conflict-logic).
	2.	Make your changes with clear, tested commits.
	3.	Add or update tests where relevant.
	4.	Open a pull request with a description of:
	•	What you changed
	•	Why it matters
	•	How it relates to the system’s mission or a current milestone

⸻

Need Help?
	•	Review the Context Primer
	•	Check the Simulation Event and Training Strategy
	•	Browse the active GitHub Projects

We’re building this as a resilient, reflective agentic system — and we’re excited to build it with you.

Finish your race. Help someone finish theirs.
