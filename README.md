# Lanterne Rouge 2026

A personal Tour de France training challenge. Finish every stage of the 2026 Tour,
ride it on the Peloton or walk it on the treadmill, both capped at one hour. The
lanterne rouge is the last rider to finish, not the winner, the one who keeps
showing up.

**Dashboard:** https://alponsirenas.github.io/lanterne-rouge/

## How it works

Two halves, one contract:

- **The dashboard** ([index.html](index.html)) is a static page served by GitHub Pages.
  It shows the 21 stage cards, the day's readiness brief, and each finished stage's
  report. It reads, it never writes.
- **The coach** ([run_morning.py](run_morning.py)) runs once each morning. It pulls
  yesterday's activity from Strava and today's readiness from Oura, scores the stage
  against its target blocks, asks the model for the verdict in the lanterne rouge
  voice, writes `status.json`, and emails the brief.

`status.json` is the single interface between them. The route, prescriptions, and
scoring targets live in [mission/stages.json](mission/stages.json), shared by both
halves. The coaching prompt is versioned at [prompts/coach.md](prompts/coach.md).
The full contract and build brief live in [CLAUDE.md](CLAUDE.md).

## Running the morning loop

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run_morning.py            # or --date YYYY-MM-DD, --no-email
```

`.env` needs: `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REFRESH_TOKEN`,
`OURA_TOKEN`, `ANTHROPIC_API_KEY`, and for the emailed brief `EMAIL_ADDRESS`,
`EMAIL_PASS` (a Gmail app password), `TO_EMAIL`. If Strava zones return 401, run
`python scripts/strava_reauth.py` once to grant the `profile:read_all` scope.

## Tests

```bash
pytest
```

## The 2025 edition

Last year's system, a multi-agent coach with TDF points simulation and fiction mode,
lives on the [`tour-2025` tag](https://github.com/alponsirenas/lanterne-rouge/tree/tour-2025)
and the `main` branch history.
