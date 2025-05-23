# About the Project
**Lanterne Rouge: An AI-First Coaching System for Endurance Athletes**

*Lanterne Rouge* is a project that began with a question:  
**What if your training plan adjusted itself every day — based on how you feel, how you’ve performed, and where you’re headed?**

It’s named after the last rider in the Tour de France — the one who finishes against all odds, not the one who finishes fastest.

---

## What We’re Building

We’re building a mission-aware, adaptive coaching system powered by AI. It observes, reasons, plans, and reflects — just like a good coach should.

- It pulls data from sources like Oura and Strava.
- It makes daily training decisions: push, ease, or recover.
- It updates your training plan based on trends and readiness.
- It explains itself using natural language, with help from an LLM.
- It logs memory and prepares to reflect on how it’s doing.

The system is modular and agentic. Each function (reasoning, planning, communication, etc.) is handled by a specialized agent — and those agents are being built by a small AI product team… which is also made of AI agents.

---

## Why We’re Building It

This is an exploration of:
- **How AI can support long-term training, not just optimize for speed**
- **How to design tools that adapt with you, not just serve you**
- **What happens when you build AI with AI — and they learn together**

---

## Core Principles

- **Mission-Locked Reasoning** — All decisions connect back to your goal
- **Transparency** — You should always know *why* it made a decision
- **Modularity** — Each agent can evolve without breaking the others
- **Reflection-First** — The system learns from its past
- **Low Friction** — It should integrate with your real-world workflow

---

## Current Status

We’re currently in **v0.3.0-dev**, focused on:
- Integrating OpenAI Codex to generate and maintain core training logic (Bannister CTL/ATL/TSB model).
- Replacing the static workout library with a GPT-driven Workout of the Day generator.
- Expanding readiness logging to include all Oura readiness contributors.
- Prototyping an n8n workflow to orchestrate data pulls, processing, and notifications.
- Building a demo harness (Streamlit stub) that runs one full daily cycle.
- Generating natural-language coaching summaries via LLMs.

---

## Built With

- Python
- Oura + Strava data APIs
- OpenAI and Anthropic LLMs
- OpenAI Codex
- n8n
- Streamlit
- A modular agent-based architecture

---

## What’s Next

1. **Wire up Codex for core logic**  
   - Commit a Codex hook and workflow to auto-generate or update Bannister model code.

2. **GPT-driven workout generator**  
   - Draft and integrate prompts that produce Workout of the Day based on current CTL/ATL/TSB and mission targets.

3. **Finalize Bannister model and tests**  
   - Implement `ctl_atl_tsb()` in `monitor.py` with full test coverage.

4. **Evaluate n8n orchestration**  
   - Prototype an n8n workflow that glues together Oura, Strava, GPT reasoning, and notifications.

5. **Demo harness & recording**  
   - Develop a Streamlit or run-all script to showcase one daily run, and record a 30–45s walkthrough.

6. **Release prep & version bump**  
   - Update version to v0.3.0 in code, tag the repo, and draft release notes summarizing new features.

Let’s see what it means to go the distance — with a system that’s training to go with you.

---

## Documentation Review Process

To ensure that our documentation remains accurate and up-to-date, we follow a structured review process. This process involves regular reviews, updates, and approvals to maintain the quality and relevance of our documentation.

### Steps for Reviewing and Updating Documentation

1. **Identify Documentation to Review**: Determine which documents need to be reviewed based on project milestones, changes in the system, or feedback from team members.

2. **Assign Reviewers**: Assign team members or GPT instances to review the identified documents. Ensure that reviewers have the necessary domain knowledge and context.

3. **Review and Annotate**: Reviewers should thoroughly read the documents, annotate any discrepancies, outdated information, or areas that need clarification.

4. **Update Content**: Based on the annotations, update the content to reflect the latest information, changes, and improvements. Ensure that the updates are clear, concise, and accurate.

5. **Approval and Integration**: Once the updates are made, the revised documents should be reviewed and approved by the Product Owner or designated approver. After approval, integrate the updated documents into the project repository.

6. **Communicate Changes**: Notify the team about the updated documentation and highlight any significant changes or new information.

7. **Regular Review Cycle**: Establish a regular review cycle (e.g., quarterly) to ensure that documentation remains current and relevant. Schedule periodic reviews and updates as part of the project workflow.

By following this process, we ensure that our documentation remains a valuable resource for the team, providing accurate and up-to-date information to support the development and maintenance of the Lanterne Rouge project.
