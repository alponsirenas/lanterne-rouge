# Beta Release Issue List

Tracking the minimum work required to launch the hosted five-user beta described in `docs/v1_implementation_plan.md`. Each item can become a GitHub issue/epic.

1. **Backend scaffold & auth**
   - Stand up FastAPI project with settings management, Pydantic schemas, and dependency-injected DB sessions.
   - Implement email+password auth (registration, login, refresh) plus admin flag.
   - Create Alembic migrations for `users`, `sessions`, and audit tables; seed one admin + one tester.
   - **Definition of done:** running server exposes `/healthz`, `/auth/register`, `/auth/login`; tests cover happy path + invalid creds; migrations reproducible via `alembic upgrade head`.
   - **User outcome:** testers have a simple onboarding path—create account, log in, and trust that access is secure.

2. **Mission data model + lifecycle**
   - Define Mission ORM (fields: name, mission_type, prep/event dates, state, points schema JSONB, timezone, constraints, notification prefs).
   - Tables: `missions` (PK id UUID, fk user_id, columns above), `mission_runs` (id UUID, mission_id, run_date, summary, workout_json, metrics_json), `event_progress` (mission_id, stage_number, type, ride_mode, points, completed_at, bonuses json). State transitions allowed: `PREP -> TRAINING -> EVENT_ACTIVE -> MISSION_COMPLETE`; automatic `TRAINING -> EVENT_ACTIVE` when `event_start` <= today, `EVENT_ACTIVE -> MISSION_COMPLETE` when `event_end` < today; manual revert only `TRAINING -> PREP` (admin).
   - Points schema JSON sample:
     ```json
     {
       "flat": {"gc": 5, "breakaway": 8},
       "mountain": {"gc": 6, "breakaway": 10},
       "itt": {"gc": 7, "breakaway": 9},
       "bonuses": {
         "consecutive_5": {"threshold": 5, "points": 5},
         "breakaway_10": {"threshold": 10, "points": 15}
       }
     }
     ```
   - Implement lifecycle service enforcing valid transitions and automatic state updates when dates pass.
   - Expose CRUD + `POST /missions/{id}/transition` endpoints guarded by auth and ownership checks.
   - **Definition of done:** DB migrations applied; API docs list mission endpoints; integration tests verify create/update/transition behavior and invalid transitions produce 400/409.
   - **User outcome:** testers can see exactly where their mission stands (prep, training, event) and trust transitions happen automatically as dates roll forward.

3. **LLM-powered Mission Builder**
   - Create questionnaire schema (availability, event goal, constraints) and endpoint `POST /missions/draft`.
   - Questionnaire fields: event name, event date, mission type (dropdown), weekly hours available (min/max), current FTP, preferred training days, constraints (injuries/time windows), desired event-mode style (gc/breakaway/steady), communication preference.
   - LLM model: **OpenAI gpt-4o-mini** (JSON mode). Prompt includes mission schema, user profile, and constraints; see `prompts/mission_builder.md` TBD for full text.
   - Example prompt snippet:
     ```
     SYSTEM: You are Lanterne Rouge mission architect...
     USER: {"event_name":"Unbound 200","event_date":"2025-06-07","weekly_hours":{"min":8,"max":12}, ...}
     ```
   - Expected response:
     ```json
     {
       "name": "Unbound 200 Prep",
       "mission_type": "gravel_ultra",
       "prep_start": "2025-03-01",
       "event_start": "2025-06-07",
       "event_end": "2025-06-07",
       "points_schema": {...},
       "constraints": {"min_readiness":70,"min_tsb":-10},
       "notes": "Focus on long aerobic blocks..."
     }
     ```
   - Prompt LLM with inputs + guardrails to return mission JSON; enforce schema via Pydantic; retry once on malformed JSON.
   - Retry strategy: immediate re-prompt with clarification + `temperature=0`; if second attempt fails, return 502 with actionable error.
   - Store draft for user to confirm/edit before saving as Mission.
   - **Definition of done:** endpoint returns validated draft JSON, includes prompt/response logging (redacted); unit tests mock LLM to cover happy + malformed cases.
   - **User outcome:** testers answer a short survey and immediately receive a personalized plan they can tweak without touching TOML or code.

4. **Data connections**
   - **Strava:** OAuth2 flow with redirect, token exchange, refresh cron, and per-user credential storage (encrypted).
   - **Oura:** secure PAT storage + validation endpoint.
   - **Apple Health:** dashboard upload endpoint accepting ZIP/XML, converts to normalized metrics saved per day.
   - **Definition of done:** user can connect each source end-to-end; sample exports produce readiness/HRV data; background refresh logs success; secrets never logged.
   - **User outcome:** testers see a single “Connections” panel showing green checks, and their data starts flowing within a minute of connecting/uploading.

5. **Tour Coach service refactor**
   - Refactor service entrypoint to accept `mission_id`, fetch metrics from connected sources, and call LLM decision/pathways.
   - EventProgress table schema: `id UUID`, `mission_id UUID`, `stage_number INT`, `stage_type TEXT`, `ride_mode TEXT`, `points INT`, `bonuses JSONB`, `completed_at TIMESTAMP`, `activity_id TEXT`.
   - LLM integration: use `gpt-4o-mini` for training decisions, `gpt-4o` fallback for event days requiring richer reasoning; enforce JSON schema defined in `schemas/coach_output.json`.
   - JSON schema includes fields `action`, `reason`, `intensity_recommendation`, `flags`, `confidence`, `recommended_ride_mode`, `mode_rationale`, `expected_points`, `bonus_opportunities`, `strategic_notes`, `workout_plan` (zones/duration).
   - Error handling: catch JSON parse errors, log prompt/response hash, retry once; if still invalid, raise incident + notify admin, skip workout for that day.
   - Sample coaching output stored in S3 and DB:
     ```json
     {
       "action": "maintain",
       "reason": "You slept well but TSB is -9...",
       "intensity_recommendation": "moderate",
       "recommended_ride_mode": "gc",
       "workout_plan": {"type":"Endurance","duration_minutes":90,"zones":{"Z2":60,"Z3":30}}
     }
     ```
   - Remove rule-based fallbacks; add JSON schema validation + retry with error reporting.
   - Implement `EventProgress` table/service tracking stages, ride modes, points, bonuses.
   - Persist run outputs (summary, workout, metrics snapshot) linked to mission/run table.
   - **Definition of done:** CLI/worker job `run_mission_day(user_id, mission_id)` completes using DB data, writes mission_run + event_progress rows, and passes unit/integration tests with mocked APIs.
   - **User outcome:** each daily run yields a coherent coaching note + workout + points update tied directly to their mission, visible moments after the job finishes.

6. **Worker & scheduler**
   - Package Celery worker within same repo (shared settings) and configure Redis broker.
   - Implement Celery Beat (or cron) task that queries missions in `TRAINING`/`EVENT_ACTIVE`, respects user timezone, enqueues daily job.
   - Add admin command to trigger manual runs for debugging.
   - **Definition of done:** `docker-compose up` brings API + worker + scheduler; logs show scheduled jobs for seeded missions; retry/backoff works on simulated failure.
   - **User outcome:** testers receive guidance automatically each morning without manual triggers; admins can rerun if something goes wrong.

7. **Dashboard MVP**
   - UI framework: **Next.js 14 + Tailwind CSS**, deployed on Vercel (free tier).
   - State/data fetching via **React Query** against `/api`.
   - API contracts documented in OpenAPI; dashboard consumes:
     - `GET /me`, `GET/POST /missions`, `POST /missions/draft`, `GET /missions/{id}/runs`, `GET /connections/status`, `POST /apple-health/upload`.
   - Implement login + mission wizard UI consuming mission builder endpoint.
   - Display connection status (Strava/Oura/Apple Health) and allow uploads.
   - Show latest run summary, readiness trend, and event-progress/points for mission.
   - Provide lightweight admin page listing users + latest runs with “rerun” button.
   - Wireframe (high-level):
     - **Hero panel**: mission name, state, next run countdown.
     - **Connections card**: Strava/Oura toggles + Apple upload button.
     - **Daily summary card**: excerpt + “view full recommendation”.
     - **Event progress table**: stage numbers, points, ride mode history.
   - **Definition of done:** deployed dashboard (Vercel or static) covering flows above, responsive on mobile, and backed by integration tests/storybook snapshots.
   - **User outcome:** testers have a single page where they can onboard, connect data, upload Apple Health files, and read daily recommendations without touching the backend.

8. **Notifications & artifacts**
   - Integrate SES/SendGrid sending daily summary emails (HTML + plaintext) per mission run; fallback email to admin on failures.
   - Email template: Subject `Lanterne Rouge Daily Brief – {Mission Name} ({Date})`; body sections for readiness summary, workout plan, event strategy; include CTA to dashboard.
   - Upload reasoning JSON, workout plan, and Apple Health files to S3 bucket `s3://lanterne-beta/{user_id}/{mission_id}/{yyyy-mm-dd}/...`; retention policy 180 days for reasoning logs, 30 days for raw Apple Health uploads.
   - **Definition of done:** sample run sends email to tester inbox, artifacts visible in bucket, and failure path triggers admin alert.
   - **User outcome:** testers wake up to email summaries even if they never open the dashboard; their historical artifacts are safely stored for later review.

9. **Instrumentation & operations**
   - Add structured logging (mission_id, run_id, data source flags), `/metrics` endpoint exporting core counters, and daily status email summarizing run results.
   - Metrics to track: `mission_runs_total{status}`, `llm_tokens_total`, `connection_refresh_failures_total`, `scheduler_jobs_enqueued`, `notification_failures_total`.
   - Provider choice: deploy on **Fly.io** (single app) with managed Postgres + Upstash Redis; monitor via Fly logs + Prometheus scraping `/metrics`.
   - Provide deployment scripts or Terraform that spin up app container + managed Postgres/Redis; document environment variables and secrets. Sample `fly.toml` + `docker-compose` included.
   - **Definition of done:** health report email hits maintainer inbox, `/metrics` shows live counters, and deployment script provisions staging env from scratch.
   - **User outcome:** reliable service—ops can detect failures quickly, keeping daily recommendations consistent for testers.

10. **Docs & beta playbook**
    - Refresh README with hosted-first messaging + link to beta guide.
    - Author tester guide (onboarding steps, connecting data, Apple Health export walkthrough) and privacy note.
    - Write maintainer runbook covering environment setup, deployment, token rotation, run inspection, and troubleshooting.
    - **Definition of done:** docs published in repo/site, reviewed with testers, and referenced during kickoff; maintainer runbook validated by dry-run.
    - **User outcome:** testers know exactly how to start, what to expect each day, and how their data is handled; maintainers have a playbook to support them.

Once these issues are delivered, the beta environment should support five testers with daily coaching, event mode, and lightweight ops visibility.***
