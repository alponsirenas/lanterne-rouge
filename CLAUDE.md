# Lanterne Rouge 2026, build brief for Claude Code

This is the 2026 edition of Lanterne Rouge, a personal Tour de France training challenge.
The goal is consistency. Finish every stage, ride it on the Peloton or walk it on the
treadmill, both capped at one hour. The lanterne rouge is the last rider to finish, not
the winner, the one who keeps showing up.

The system has two halves:

1. The dashboard. A static HTML page (`index.html`) that shows the 21 stage cards, the
   day's readiness, and the result of each finished stage. It reads, it never writes.
2. The coach. A morning backend loop that pulls the day's data, scores the stage, and
   writes one file the dashboard reads.

## The contract

`status.json` is the single interface between the two halves. The backend writes it, the
dashboard reads it. Do not change a field on one side without changing the other. Keep the
dashboard read only. All judgment lives in the backend.

Schema:

```
{
  "updated": "ISO timestamp of the last run",
  "today": {
    "date": "YYYY-MM-DD",
    "stage": <stage number or null on a rest day>,
    "readiness": { "score": int, "sleep_score": int, "resting_hr": int, "hrv": int, "sleep_hours": float },
    "recommendation": "push | ease | recover",
    "note": "one or two plain sentences from the coach"
  },
  "stages": {
    "s1": {
      "status": "finished | missed | upcoming",
      "completed_via": "ride | walk | null",
      "strava": {
        "duration_min": int, "distance_km": float,
        "avg_hr": int, "max_hr": int, "avg_watts": int or null,
        "relative_effort": int,
        "time_in_zone": { "z1": min, "z2": min, "z3": min, "z4": min, "z5": min }
      },
      "oura": { "readiness": int, "sleep_score": int, "resting_hr": int, "hrv": int, "sleep_hours": float },
      "verdict": { "call": "push | ease | recover", "hit_target": bool, "note": "one or two sentences" }
    }
  }
}
```

Notes on the schema. Before the first morning run, `today` may carry only `date` and
`stage`; the dashboard shows no brief until `readiness` arrives, and never invents one.
Walks have `avg_watts: null` and the zones are heart-rate based. A
missed stage has `strava: null` and must still carry a `verdict`; `oura` is optional.
Every finished or missed stage carries a `verdict`, the dashboard renders it without
guarding. A stage that has not happened yet may be absent from `stages` or present as
`{"status": "upcoming"}`; both mean the same thing. The dashboard derives the finished
count and the current stage from this file alone.

## The morning loop

One run, once a day, in this order:

1. Pull yesterday's activity from Strava. Match it to the stage by date. A ride is a
   Peloton effort, a walk or run is a treadmill effort. Either one finishes the stage.
2. Pull today's readiness from Oura: readiness, sleep, resting heart rate, HRV.
3. Score the finished stage. Use the athlete's Strava zones to turn the streams into
   time in zone, and check whether the prescribed blocks were held.
4. Decide push, ease, or recover for today from readiness and recent load.
5. Write the verdict in plain language, in the lanterne rouge voice. Finishing over
   performance, no hype.
6. Write `status.json` with `today.date` set to the actual date of the run. The
   dashboard compares that date to the device date and shows a stale warning when they
   differ, so the loop should run before the day's workout.

Later, also deliver the brief by email or to Notion.

## Mission config

The route and the prescriptions are the single source of truth and must be shared by both
halves. Keep them in a versioned file (`mission/stages.json`), read by the dashboard and
the backend. Each stage carries: number, date, route, type, the ride prescription, the
walk prescription, the target blocks the scorer checks against, and the map geometry the
dashboard's map view uses (start and finish coordinates, plus the marker pixel offset for
finishes that share a town). Do not hardcode stage data in two places. Pure drawing data,
the coastline, the border, town and range labels, and the key, is presentation and stays
in the dashboard.

## Standing principles

These carry over from the original Lanterne Rouge and still hold.

- Radical simplicity. Prefer deleting code to adding it. A script and a few modules
  stitched with intent beats a framework.
- AI native, not rule trees. Let the model read the data and write the verdict. Do not
  build a large branching rule engine to imitate judgment.
- Prompts are versioned files. The coaching prompt lives in `prompts/coach.md`, not inline
  in a string. Change it like code, in commits.
- Stage the rollout. Ship v0, then v1, then v2. Do not build v2 first.
- Watch the scaffolding. Every helper and config you add is something to maintain. If you
  cannot say why a file exists, remove it.
- Human in the loop for anything irreversible. Sending messages and writing to shared
  surfaces should be reviewable before they go fully automatic.
- Never invent data. If Oura or Strava is missing for a day, write the status to reflect
  that, finished without context, or missed, rather than guessing.

## Staged rollout

- v0, done. The dashboard reads a hand-written `status.json`. This validates the contract
  and the visuals. The current dashboard lives as `lanterne-rouge-2026.html` and falls
  back to a built-in sample when no file is served. Rename it to `index.html` when it
  moves into the repo.
- v1. A script pulls Strava and Oura, matches the stage, scores it, and writes a real
  `status.json`. Run it by hand each morning. No scheduling, no delivery yet.
- v2. Schedule the run, on Anthropic's cloud as a routine or as a GitHub Action, add the
  email or Notion delivery, and move the coaching logic fully into `prompts/coach.md`.

## Suggested layout

```
index.html            the dashboard, reads status.json
status.json           the state, written by the backend
mission/stages.json   the route and prescriptions, shared source of truth
prompts/coach.md      the versioned coaching prompt
src/monitor.py        pull Strava and Oura
src/reason.py         score the stage, decide push/ease/recover, write the verdict
run_morning.py        the loop that ties it together and writes status.json
```

## Hosting

The dashboard fetches `status.json` over HTTP, so it must be served, not opened as a local
file. GitHub Pages is the natural home since the repo already lives there. The morning job
commits the new `status.json`, and the page reads it from a URL you can open from anywhere,
which also means completion follows you across phone and laptop instead of living in one
browser.

## Data sources

- Strava: activity, heart rate, power, relative effort, streams, and athlete zones.
- Oura: readiness, sleep, resting heart rate, HRV.

Same two sources as last year.
