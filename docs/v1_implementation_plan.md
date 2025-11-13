# Lanterne Rouge v1.0 Beta Implementation Plan

This plan focuses on the **beta launch for five testers**, delivering a lean hosted version of Tour Coach that still honors the training-season + event-mode lifecycle. Anything beyond this beta scope (e.g., public release, large-scale multi-tenancy, advanced observability) is explicitly out of scope for this document.

---

## 1. Product Goals & Non-Goals

**Goals (Beta)**
- Deliver a lightweight hosted experience where five testers authenticate, connect Strava/Oura or upload Apple Health exports, create missions with LLM support, and receive daily guidance.
- Preserve the two-phase lifecycle: _Training Season_ → _Event Mode_ with points/gameplay so testers can prep and “race” their own events.
- Keep all decisions LLM-authored while providing simple guardrails (JSON validation + retries).
- Instrument just enough telemetry (structured logs + basic metrics) to debug failures and learn from usage.

**Out of Scope for Beta**
- Multi-mission concurrency per user, large-scale tenancy, or enterprise auth.
- Fiction Mode publishing, GitHub automation, or advanced documentation tooling.
- Full Apple Health companion app (manual export upload only during beta).

---

## 2. High-Level Architecture (Beta)

| Component | Responsibility | Notes |
|-----------|----------------|-------|
| **FastAPI service** | Auth, mission CRUD, simple dashboard APIs, Strava/Oura OAuth callbacks, Apple Health export ingestion | Runs on a single container alongside worker processes. |
| **Background worker (Celery/RQ)** | Executes Tour Coach runs per mission (training + event mode) | Shares code + container with API; pulls jobs from Redis-lite queue. |
| **Scheduler** | Nightly cron/beat job that enqueues one run per active mission | Implemented via Celery Beat or OS cron; timezone offsets handled in app logic. |
| **PostgreSQL (starter tier)** | Stores users, missions, mission runs, event progress, connection metadata | Managed service (Render/Supabase/etc.). |
| **Redis-lite queue** | Lightweight broker for job dispatch/retries | Managed or containerized instance. |
| **Static dashboard (Next.js or lightweight React)** | Mission wizard + run history view | Can be hosted on Vercel or served statically from the FastAPI app. |
| **Object storage (S3-compatible)** | Reasoning logs, Apple Health uploads, generated summaries | Single bucket with lifecycle policies. |

Legacy scripts (`scripts/daily_run.py`, GitHub-secret updates, local SQLite caches) are refactored into worker modules invoked through the API stack.

### 2.1 Data Source Strategy
- **Strava**: Continue using OAuth 2.0 for activity detail and power metrics; workers refresh tokens and sync activities daily.
- **Oura**: Maintain Personal Access Token flow for readiness, sleep, and HRV; schedule refreshes alongside daily runs.
- **Apple Health (beta)**:
  - Support manual upload of Apple Health exports (ZIP/XML → JSON) through the dashboard; parse key metrics server-side.
  - Document the future Swift/SwiftUI companion but defer implementation until GA.
  - Track Apple Health connection metadata alongside other sources to keep APIs uniform.

### 2.2 Lean Beta Deployment (5 users)
- Run API + worker processes on a single container/VM (e.g., Fly.io/Railway/Render) with at least 2 vCPU / 4 GB RAM; scale horizontally only after beta feedback.
- Use managed “starter” tiers for PostgreSQL (~$25/mo) and Redis-lite (~$10/mo), or containerized equivalents on the same host.
- Keep S3-compatible storage minimal (few GB) for reasoning logs + Apple Health uploads.
- Instrumentation can remain lightweight (structured logs + Prometheus on the same host) until more users demand full observability.
- Notifications limited to email (SES/SendGrid free tiers) to avoid Twilio/SMS charges.
- Apple Health companion app deferred; rely on manual export ingestion for early testers to avoid Apple Developer Program costs.

---

## 3. Mission Lifecycle & LLM Mission Builder

### 3.1 Lifecycle States
Each mission transitions through the following states:
1. `PREP`: Mission configured but not started; user can edit details.
2. `TRAINING`: Mission active before goal event; Tour Coach issues training guidance.
3. `EVENT_ACTIVE`: Current date within event window; Tour Coach switches to event prompts, stage recommendations, and point tracking.
4. `MISSION_COMPLETE`: Event window finished; LLM produces a wrap-up reflection, mission locks for edits.
5. `ARCHIVED` (optional later): Historical record retained but not runnable.

The scheduler selects the mission whose state is `TRAINING` or `EVENT_ACTIVE` for a user on a given day and triggers a worker job with that mission context.

### 3.2 Mission Model Changes
- Extend `MissionConfig` (or successor ORM model) with:
  - `mission_type` (e.g., `road_stage_race`, `gravel_ultra`, `tt_series`).
  - `prep_start`, `event_start`, `event_end`.
  - `points_schema` + `stage_plan` metadata for event mode.
  - `llm_goal_statement` and `constraints` captured from onboarding.
  - Notification preferences, timezone, and preferred contact methods.
- Replace TOML loading/caching with DB-backed retrieval. Workers request `Mission` objects via internal API/service.

### 3.3 LLM-Assisted Mission Builder
1. User initiates “Create Mission” wizard (web UI).
2. Collect structured inputs: event name/date, training availability, rider profile, goals, safety constraints.
3. Call new `MissionBuilder` module that prompts the LLM to produce a JSON mission draft (aligned with schema).
4. Validate via Pydantic; if invalid, display issues and allow user edits before saving.
5. Persist mission to DB, set initial state to `PREP`, and enqueue onboarding summary email generated by LLM.

---

## 4. Backend & Service Implementation

### 4.1 Data Layer
- Migrate mission definitions, readiness logs, TDF points, and run history from local files/SQLite into PostgreSQL tables:
  - `users`, `missions`, `mission_runs`, `connections` (Strava/Oura), `tdf_progress` (generalized to `event_progress`), `notifications`.
- Store bulky artifacts (reasoning logs, narrative exports) in object storage or append-only tables keyed by `mission_id`.

### 4.2 Tour Coach Refactor
- `TourCoach` and `ReasoningAgent` accept mission objects + lifecycle state (including selected data source: Strava, Oura, or Apple Health) instead of reading from TOML/`tdf_tracker`.
- Remove rule-based fallbacks; add robust LLM error handling (retry logic, schema validation, guardrails).
- Expose new entrypoint for worker jobs: `run_mission_day(user_id, mission_id, date)` that orchestrates metric fetching, LLM prompts, workout plan creation, event-mode logic, and persistence.

### 4.3 API Surface
- **User endpoints**: signup/login, connect Strava/Oura (OAuth), link OpenAI API key if BYO.
- **Mission endpoints**: create/edit via LLM builder, start mission, view status/history, trigger manual run, mark completion.
- **Admin endpoints**: monitor job queue, inspect mission runs, manage feature flags.

### 4.4 Scheduler & Workers
- Implement daily scheduler aware of user timezones; leverages Celery beat/RQ scheduler.
- Worker job flow:
  1. Fetch mission + user secrets.
  2. Pull latest Strava/Oura data; refresh tokens if needed.
  3. Query historical context (memories, event progress) scoped to mission.
  4. Execute `TourCoach` with mission state (training vs. event).
  5. Persist outputs (summary, workout prescription, event points).
  6. Send notifications via configured channels.

### 4.5 Points/Event Tracking
- Generalize `TDFTracker` into `EventProgressService` storing per-mission stage completions, ride modes, points, and bonus achievements inside the DB. Workers update it after each event-mode run.

---

## 5. Instrumentation & Observability

1. **Structured Logging (built-in)**: JSON logs streamed to stdout and persisted in object storage; include mission/user IDs, run status, LLM model, and error traces.
2. **Lightweight Metrics**: Expose `/metrics` with Prometheus client on the API host (runs succeeded/failed, LLM call counts, queue depth). Optional single-node Prometheus scrapes itself.
3. **Simple Alerts**: Daily cron checks for failed runs or stale missions and emails the maintainer; no paging system needed in beta.
4. **Manual Dashboards**: Basic admin page (or notebook) reading from Postgres to inspect user activity and points.
5. **Upgrade Path**: Document how to layer in full OpenTelemetry/managed observability post-beta.

---

## 6. Rollout & Testing Strategy

### 6.1 Development Phases
1. **Foundation (Sprint 1-2)**: Stand up backend scaffold, DB schema, auth, and mission models. Implement Mission Builder MVP with LLM output validation.
2. **Tour Coach Service (Sprint 3-4)**: Refactor worker entrypoint, integrate metrics ingestion, LLM-only reasoning, and event progress service.
3. **Dashboard & Onboarding (Sprint 5)**: Build mission wizard UI, connection flows, run history views.
4. **Instrumentation & Ops (Sprint 6)**: Telemetry pipeline, admin monitoring, alerting.
5. **Beta Hardening (Sprint 7)**: Load testing, fail-safe handling for API outages, DR routines, documentation updates.

### 6.2 Testing
- Unit tests for mission builder validation, mission lifecycle transitions, and event progress calculations.
- Integration tests for worker jobs (mock Strava/Oura/LLM).
- End-to-end tests for mission creation → daily run → notifications using staging credentials.
- Chaos/testing hooks to simulate LLM failures and ensure retries without rule-based fallback.

### 6.3 Migration / Legacy Support
- Provide a script to import existing TOML missions + `tdf_points.json` into the new DB schema for the primary user.
- Keep CLI entrypoints available for internal testing, but mark them as developer tools; hosted flow becomes canonical.

---

## 7. Documentation & Communication

- Update `README.md` to reflect hosted service positioning, linking to beta portal docs.
- Create user-facing docs covering onboarding, mission creation, data privacy, and event mode behavior.
- Maintain this implementation plan in `docs/v1_implementation_plan.md` and iterate as architecture decisions evolve.

---

## 8. Recommended Tech Stack

| Layer | Recommendation | Rationale |
|-------|----------------|-----------|
| Backend API | **FastAPI** | Matches current Python stack, fast to iterate, easy JSON validation for LLM + mission builder. |
| ORM & Migrations | **SQLAlchemy + Alembic** | Lightweight schema management suitable for beta data models. |
| Database | **Managed PostgreSQL starter tier** | Enough for five users, easy backups, low operational overhead. |
| Workers & Scheduler | **Celery (Redis broker + Beat)** | Simple to run inside same container; retries + scheduling included. |
| Frontend | **Minimal Next.js/React SPA** | Wizard + history view; can be deployed via Vercel free tier. |
| Secrets Management | **Environment variables + encrypted DB columns** | Adequate for beta; upgrade to Vault/Secrets Manager later. |
| Object Storage | **Single S3-compatible bucket** | Stores reasoning logs, attachments, Apple Health uploads. |
| Observability | **Prometheus client + structured logs** | Meets beta needs; paves path to full OpenTelemetry later. |
| Apple Health Bridge | **Manual export uploader** | No Apple dev app yet; keeps complexity and cost low. |

This lean stack minimizes spend while keeping migration paths open for a production-scale release.

---

## 9. Beta Cost Baseline (5 Active Users)

| Item | Estimate (monthly) | Notes |
|------|-------------------|-------|
| Compute (API + worker on single host) | $40 | Fly.io/Railway/Render 2 vCPU / 4 GB instance. |
| PostgreSQL starter tier | $25 | Managed DB (Render/Supabase/Railway). |
| Redis lite / task queue | $10 | Small cache/queue instance or shared container. |
| Object storage + bandwidth | $5 | S3-compatible bucket for logs/exports. |
| Email notifications | $0–5 | Within SES/SendGrid free tier. |
| LLM usage | $15 | GPT‑4o‑mini (or similar) for 5 runs/day + mission builder calls. |
| Monitoring/logging | $5 | Lightweight metrics/logs on same host. |
| Contingency | $10 | Covers overages/paid add-ons. |
| **Total** | **≈ $110/mo** | Recurring cost for 5 beta users. |

One-time costs remain limited to engineering time. Incremental expenses (Twilio SMS, Apple Developer Program, larger DB tiers, higher-end LLMs) only kick in when user count or feature set expands.

---

_Last updated: {{DATE TBD}}_
