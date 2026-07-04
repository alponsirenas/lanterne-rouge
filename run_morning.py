#!/usr/bin/env python3
"""The morning loop, one run a day before the workout.

Pulls yesterday's activity from Strava and today's readiness from Oura, scores the
finished stage against its target blocks, asks the coach for the verdicts, writes
status.json, and emails the brief. Safe to re-run, it overwrites the same day.
"""

import argparse
import json
import os
import smtplib
import sys
from datetime import date, datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import monitor  # noqa: E402
import reason  # noqa: E402

MISSION_PATH = ROOT / "mission" / "stages.json"
STATUS_PATH = ROOT / "status.json"


def load_mission() -> dict:
    return json.loads(MISSION_PATH.read_text(encoding="utf-8"))


def stage_on(mission: dict, day: date) -> dict | None:
    iso = day.isoformat()
    return next(
        (s for s in mission["stages"] if not s.get("rest") and s["date"] == iso),
        None,
    )


def is_rest_day(mission: dict, day: date) -> bool:
    iso = day.isoformat()
    return any(s.get("rest") and s["date"] == iso for s in mission["stages"])


def build_stage_entry(detail, via, tiz, oura, hit, verdict) -> dict:
    """One entry of status.json's stages map, per the contract in CLAUDE.md."""
    if detail is None:
        entry = {"status": "missed", "completed_via": None, "strava": None}
    else:
        entry = {
            "status": "finished",
            "completed_via": via,
            "strava": monitor.strava_summary(detail, tiz, via),
        }
    if oura:
        entry["oura"] = oura
    entry["verdict"] = {
        "call": verdict.get("call", "ease"),
        # a miss is never on target; None means finished without zone context
        "hit_target": False if detail is None else hit,
        "note": verdict.get("note", ""),
    }
    return entry


def build_payload(mission, today, today_stage, readiness, y_stage, y_detail, y_via,
                  y_tiz, y_oura, y_hit, call_that_morning, status) -> dict:
    def stage_brief(s):
        return {
            "n": s["n"], "route": s["route"], "type": s["type"], "note": s["note"],
            "ride_min": s["rideMin"], "ride": s["ride"],
            "walk_min": s["walkMin"], "walk": s["walk"],
        }

    yesterday = None
    if y_stage:
        yesterday = {
            "stage": stage_brief(y_stage),
            "targets": y_stage["targets"],
            "completed_via": y_via,
            "activity": monitor.strava_summary(y_detail, y_tiz, y_via) if y_detail else None,
            "readiness_that_morning": y_oura,
            "hit_target": y_hit,
            "call_that_morning": call_that_morning,
        }

    recent = []
    for s in mission["stages"]:
        if s.get("rest"):
            continue
        rep = status.get("stages", {}).get(s["id"])
        if rep and rep.get("status") in ("finished", "missed") and rep.get("verdict"):
            recent.append({
                "stage": s["n"],
                "status": rep["status"],
                "call": rep["verdict"].get("call"),
                "note": rep["verdict"].get("note"),
            })
    return {
        "today": {
            "date": today.isoformat(),
            "rest_day": is_rest_day(mission, today),
            "stage": stage_brief(today_stage) if today_stage else None,
            "readiness": readiness,
        },
        "yesterday": yesterday,
        "recent": recent[-4:],
    }


def send_brief(status, mission, today, today_stage):
    addr, password, to = os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASS"), os.getenv("TO_EMAIL")
    if not (addr and password and to):
        print("Email not configured (EMAIL_ADDRESS, EMAIL_PASS, TO_EMAIL), skipping.")
        return

    t = status["today"]
    lines = []
    if today_stage:
        subject_what = f"Stage {today_stage['n']}"
        lines.append(f"Stage {today_stage['n']} · {today_stage['route']} · {today_stage['day']}")
        lines.append(f"{today_stage['km']} on the road. {today_stage['note']}")
    elif is_rest_day(mission, today):
        subject_what = "Rest day"
        lines.append("Rest day. Full rest, or twenty easy minutes and some mobility.")
    else:
        subject_what = "No stage today"
        lines.append("No stage on the card today.")

    if t.get("readiness"):
        r = t["readiness"]
        bits = [f"Readiness {r['score']}"] if r.get("score") is not None else []
        if r.get("sleep_hours") is not None:
            bits.append(f"slept {r['sleep_hours']} h")
        if r.get("resting_hr") is not None:
            bits.append(f"resting HR {r['resting_hr']}")
        if r.get("hrv") is not None:
            bits.append(f"HRV {r['hrv']}")
        lines.append("")
        lines.append(" · ".join(bits))
    if t.get("recommendation"):
        lines.append("")
        lines.append(f"{t['recommendation'].upper()} — {t.get('note', '')}")
    if today_stage:
        lines.append("")
        lines.append(f"Ride, {today_stage['rideMin']} min: {today_stage['ride']}")
        lines.append(f"Walk, {today_stage['walkMin']} min: {today_stage['walk']}")

    y_stage = stage_on(mission, today - timedelta(days=1))
    if y_stage:
        rep = status.get("stages", {}).get(y_stage["id"])
        if rep and rep.get("verdict"):
            v = rep["verdict"]
            lines.append("")
            if rep["status"] == "finished":
                how = "by bike" if rep.get("completed_via") == "ride" else "on foot"
                tgt = ""
                if isinstance(v.get("hit_target"), bool):
                    tgt = ", on target" if v["hit_target"] else ", off target"
                lines.append(f"Yesterday, stage {y_stage['n']} ({y_stage['route']}): finished {how}{tgt}.")
            else:
                lines.append(f"Yesterday, stage {y_stage['n']} ({y_stage['route']}): missed.")
            lines.append(f"{v['call'].upper()} — {v['note']}")

    url = os.getenv("DASHBOARD_URL")
    if url:
        lines.append("")
        lines.append(url)

    rec = t.get("recommendation")
    subject = f"Lanterne Rouge · {subject_what}" + (f" · {rec}" if rec else "")
    msg = MIMEText("\n".join(lines))
    msg["Subject"] = subject
    msg["From"] = addr
    msg["To"] = to
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(addr, password)
            server.send_message(msg)
        print(f"Brief emailed to {to}.")
    except (smtplib.SMTPException, OSError) as exc:
        # the brief is a courtesy; status.json is already written
        print(f"Email failed, dashboard still updated: {exc}")


def main():
    ap = argparse.ArgumentParser(description="Run the Lanterne Rouge morning loop.")
    ap.add_argument("--date", help="Run as if today were YYYY-MM-DD (for testing).")
    ap.add_argument("--no-email", action="store_true", help="Skip the email brief.")
    args = ap.parse_args()

    today = date.fromisoformat(args.date) if args.date else date.today()
    yesterday = today - timedelta(days=1)
    mission = load_mission()
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8")) if STATUS_PATH.exists() else {"stages": {}}
    status.setdefault("stages", {})

    today_stage = stage_on(mission, today)
    y_stage = stage_on(mission, yesterday)

    # 1-2. pull the facts
    readiness = monitor.readiness_for(today)
    y_detail = y_via = y_tiz = y_oura = None
    y_hit = None
    if y_stage:
        y_detail, y_via = monitor.activity_for(yesterday)
        if y_detail:
            y_tiz = monitor.time_in_zone(y_detail["id"], monitor.hr_zones())
        y_oura = monitor.readiness_for(yesterday)
        y_hit = reason.hit_target(y_stage["targets"], y_tiz) if y_detail else False
        print(f"Stage {y_stage['n']} yesterday: "
              + (f"{y_via}, {round(y_detail['moving_time'] / 60)} min, zones {y_tiz}" if y_detail else "no activity logged"))

    # the call made yesterday morning becomes the stage's verdict call
    prev_today = status.get("today", {})
    call_that_morning = (
        prev_today.get("recommendation")
        if prev_today.get("date") == yesterday.isoformat() else None
    )

    # 3-5. score and write the verdicts
    verdict = {"yesterday": None, "today": {}}
    if y_stage or readiness:
        payload = build_payload(mission, today, today_stage, readiness, y_stage,
                                y_detail, y_via, y_tiz, y_oura, y_hit,
                                call_that_morning, status)
        verdict = reason.coach(payload)

    if y_stage:
        status["stages"][y_stage["id"]] = build_stage_entry(
            y_detail, y_via, y_tiz, y_oura, y_hit,
            verdict.get("yesterday") or {},
        )

    today_block = {"date": today.isoformat(), "stage": today_stage["n"] if today_stage else None}
    if readiness and verdict.get("today"):
        today_block["readiness"] = readiness
        today_block["recommendation"] = verdict["today"].get("recommendation", "ease")
        today_block["note"] = verdict["today"].get("note", "")
    status["today"] = today_block
    status["updated"] = datetime.now().astimezone().isoformat(timespec="seconds")

    # 6. write the one file the dashboard reads
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {STATUS_PATH.relative_to(ROOT)} for {today.isoformat()}"
          + (f", stage {today_stage['n']}" if today_stage else ", rest day"))

    if not args.no_email:
        send_brief(status, mission, today, today_stage)


if __name__ == "__main__":
    main()
