# Activity-Triggered Evening Workflow Design

## Overview

Replace the scheduled evening points summary with an activity-triggered system that responds immediately when new Strava activities are logged, providing instant feedback on points earned and bonus progress.

## Current Architecture Integration

**Existing Flow:**
```
Daily Schedule → daily_run.py → Morning Briefing → [Manual Workout] → [No Immediate Feedback]
```

**Enhanced Flow:**
```
Daily Schedule → daily_run.py → Morning Briefing → [Manual Workout] → Strava Activity → Evening Summary
```

## Implementation Approaches

### Approach 1: Strava Webhooks (Recommended)

#### 1.1 Webhook Infrastructure
**New file**: `src/lanterne_rouge/webhook_server.py`

```python
from flask import Flask, request, jsonify
import hmac
import hashlib
import os
from datetime import datetime
import threading

app = Flask(__name__)

class StravaWebhookHandler:
    """Handles Strava webhook events for activity creation."""
    
    def __init__(self):
        self.verify_token = os.getenv("STRAVA_VERIFY_TOKEN", "lanterne_rouge_2025")
        self.webhook_secret = os.getenv("STRAVA_WEBHOOK_SECRET")
        
    def verify_webhook(self, payload: str, signature: str) -> bool:
        """Verify webhook signature for security."""
        if not self.webhook_secret:
            return True  # Skip verification in development
            
        expected_sig = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_sig}", signature)

@app.route("/webhook/strava", methods=["GET"])
def webhook_challenge():
    """Handle Strava webhook verification challenge."""
    challenge = request.args.get("hub.challenge")
    verify_token = request.args.get("hub.verify_token")
    
    handler = StravaWebhookHandler()
    if verify_token == handler.verify_token:
        return jsonify({"hub.challenge": challenge})
    return "Forbidden", 403

@app.route("/webhook/strava", methods=["POST"])
def webhook_event():
    """Handle Strava webhook events."""
    handler = StravaWebhookHandler()
    
    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not handler.verify_webhook(request.get_data(as_text=True), signature):
        return "Unauthorized", 401
    
    data = request.get_json()
    
    # Only process activity creation events
    if (data.get("object_type") == "activity" and 
        data.get("aspect_type") == "create"):
        
        # Process in background to avoid webhook timeout
        threading.Thread(
            target=process_new_activity,
            args=(data.get("object_id"),),
            daemon=True
        ).start()
        
        return jsonify({"status": "ok"})
    
    return jsonify({"status": "ignored"})

def process_new_activity(activity_id: int):
    """Process new activity in background thread."""
    try:
        from .evening_tdf_processor import process_completed_stage
        process_completed_stage(activity_id)
    except Exception as e:
        print(f"Error processing activity {activity_id}: {e}")

if __name__ == "__main__":
    # Run webhook server
    app.run(host="0.0.0.0", port=int(os.getenv("WEBHOOK_PORT", 5000)))
```

#### 1.2 Webhook Setup Script
**New file**: `scripts/setup_strava_webhook.py`

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def setup_webhook():
    """Register webhook with Strava API."""
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    callback_url = os.getenv("WEBHOOK_CALLBACK_URL")  # e.g., https://your-domain.com/webhook/strava
    verify_token = os.getenv("STRAVA_VERIFY_TOKEN", "lanterne_rouge_2025")
    
    if not all([client_id, client_secret, callback_url]):
        print("Missing required environment variables for webhook setup")
        return
    
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "callback_url": callback_url,
        "verify_token": verify_token
    }
    
    response = requests.post(
        "https://www.strava.com/api/v3/push_subscriptions",
        data=data
    )
    
    if response.status_code == 201:
        print(f"✅ Webhook registered successfully: {response.json()}")
    else:
        print(f"❌ Webhook registration failed: {response.text}")

if __name__ == "__main__":
    setup_webhook()
```

### Approach 2: Activity Polling (Fallback/Alternative)

#### 2.1 Activity Monitor Service
**New file**: `src/lanterne_rouge/activity_monitor.py`

```python
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from .strava_api import strava_get
from .memory_bus import DB_FILE

class ActivityMonitor:
    """Monitors for new Strava activities and triggers evening workflow."""
    
    def __init__(self, poll_interval: int = 300):  # 5 minutes
        self.poll_interval = poll_interval
        self.last_check = self._get_last_check_time()
        
    def _get_last_check_time(self) -> datetime:
        """Get last activity check time from database."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.execute(
                "SELECT value FROM app_state WHERE key = 'last_activity_check'"
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return datetime.fromisoformat(row[0])
        except:
            pass
            
        # Default to 24 hours ago
        return datetime.now() - timedelta(hours=24)
    
    def _update_last_check_time(self, timestamp: datetime):
        """Update last check time in database."""
        conn = sqlite3.connect(DB_FILE)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.execute(
            "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
            ("last_activity_check", timestamp.isoformat())
        )
        conn.commit()
        conn.close()
    
    def check_for_new_activities(self) -> list:
        """Check for activities since last check."""
        print(f"🔍 Checking for activities since {self.last_check}")
        
        # Get recent activities
        activities = strava_get("athlete/activities?per_page=10")
        if not activities:
            return []
        
        new_activities = []
        current_time = datetime.now()
        
        for activity in activities:
            # Parse activity start time
            try:
                start_time = datetime.fromisoformat(
                    activity["start_date_local"].replace("Z", "+00:00")
                ).replace(tzinfo=None)
                
                if start_time > self.last_check:
                    new_activities.append(activity)
                    
            except (ValueError, KeyError):
                continue
        
        if new_activities:
            print(f"🎉 Found {len(new_activities)} new activities")
            self._update_last_check_time(current_time)
            
        return new_activities
    
    def start_monitoring(self):
        """Start continuous activity monitoring."""
        print(f"🎯 Starting activity monitor (checking every {self.poll_interval}s)")
        
        while True:
            try:
                new_activities = self.check_for_new_activities()
                
                for activity in new_activities:
                    from .evening_tdf_processor import process_completed_stage
                    process_completed_stage(activity["id"])
                    
            except Exception as e:
                print(f"❌ Error in activity monitoring: {e}")
            
            time.sleep(self.poll_interval)

def run_activity_monitor():
    """Entry point for activity monitoring daemon."""
    monitor = ActivityMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    run_activity_monitor()
```

#### 2.2 Activity Monitor Service Script
**New file**: `scripts/run_activity_monitor.py`

```python
#!/usr/bin/env python3
"""
Activity monitoring daemon that checks for new Strava activities
and triggers the evening TDF workflow.
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from lanterne_rouge.activity_monitor import run_activity_monitor

if __name__ == "__main__":
    run_activity_monitor()
```

### Approach 3: Evening TDF Processor (Core Logic)

#### 3.1 Evening Workflow Processor
**New file**: `src/lanterne_rouge/evening_tdf_processor.py`

```python
"""
Evening TDF workflow processor that calculates points and generates summaries
when new activities are detected.
"""

import os
from datetime import date, datetime
from typing import Dict, Any, Optional
from .strava_api import strava_get
from .memory_bus import get_current_points, log_tdf_stage
from .points_calculator import PointsCalculator
from .stage_calendar import StageCalendar
from .ai_clients import TDFCommunicationAgent
from .mission_config import bootstrap
from scripts.notify import send_email, send_sms

def process_completed_stage(activity_id: int):
    """
    Process a completed stage when a new Strava activity is detected.
    
    Args:
        activity_id: Strava activity ID that was just completed
    """
    print(f"🎉 Processing completed stage for activity {activity_id}")
    
    try:
        # Get the activity details
        activity = get_activity_details(activity_id)
        if not activity:
            print(f"❌ Could not fetch activity {activity_id}")
            return
        
        # Check if this activity qualifies as a TDF stage
        stage_info = determine_stage_info(activity)
        if not stage_info:
            print(f"ℹ️  Activity {activity_id} does not qualify as a TDF stage")
            return
        
        # Calculate points and update totals
        points_result = calculate_stage_points(activity, stage_info)
        
        # Generate and send evening summary
        summary = generate_evening_summary(activity, stage_info, points_result)
        
        # Send notifications
        send_evening_notifications(summary)
        
        # Log to memory bus
        log_stage_completion(activity, stage_info, points_result)
        
        print("✅ Evening TDF workflow completed successfully")
        
    except Exception as e:
        print(f"❌ Error processing completed stage: {e}")
        # Could send error notification here

def get_activity_details(activity_id: int) -> Optional[Dict[str, Any]]:
    """Fetch detailed activity information from Strava."""
    activity = strava_get(f"activities/{activity_id}")
    
    if not activity:
        return None
    
    # Verify this is a cycling activity
    if activity.get("sport_type") not in ["Ride", "VirtualRide"]:
        return None
        
    return activity

def determine_stage_info(activity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Determine if this activity represents a TDF stage and what type.
    
    This function needs to be smart about recognizing indoor TDF simulation
    workouts vs. regular training rides.
    """
    # Load mission config to get simulation dates
    mission_cfg = bootstrap("missions/tdf_sim_2025.toml")
    
    # Check if we're within the TDF simulation period
    activity_date = datetime.fromisoformat(
        activity["start_date_local"].replace("Z", "")
    ).date()
    
    # Initialize stage calendar
    stage_calendar = StageCalendar(mission_cfg.goal_date)  # Using goal_date as simulation start
    
    # Get today's expected stage
    expected_stage = stage_calendar.get_today_stage(activity_date)
    if not expected_stage:
        return None
    
    # Check activity characteristics to confirm it's a TDF stage
    duration_minutes = activity.get("moving_time", 0) / 60
    
    # Basic heuristics for stage recognition
    # This could be enhanced with name pattern matching, etc.
    if duration_minutes < 30:  # Too short to be a stage
        return None
    
    # For now, assume any qualifying ride during TDF period is a stage
    # Could add more sophisticated detection based on:
    # - Activity name patterns
    # - Duration thresholds
    # - Power/intensity patterns
    # - Manual stage confirmation
    
    return {
        "stage_number": expected_stage["stage_number"],
        "stage_type": expected_stage["stage_type"],
        "activity_duration": duration_minutes,
        "activity_date": activity_date
    }

def determine_ride_mode(activity: Dict[str, Any], stage_info: Dict[str, Any]) -> str:
    """
    Determine which ride mode was actually completed based on activity data.
    
    This could use intensity, duration, power patterns, etc. to classify
    whether the athlete rode in GC or Breakaway mode.
    """
    # For now, use simple heuristics based on intensity/duration
    # This could be enhanced with more sophisticated analysis
    
    duration = stage_info["activity_duration"]
    avg_power = activity.get("average_watts", 0)
    intensity_factor = activity.get("intensity_factor", 0)
    
    # Simple classification based on intensity
    # This should match the morning recommendation logic
    if intensity_factor > 0.8 or activity.get("suffer_score", 0) > 100:
        return "breakaway"
    else:
        return "gc"

def calculate_stage_points(
    activity: Dict[str, Any], 
    stage_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate points earned for the completed stage."""
    
    # Determine actual ride mode completed
    actual_mode = determine_ride_mode(activity, stage_info)
    
    # Calculate base points
    calculator = PointsCalculator()
    stage_points = calculator.calculate_stage_points(
        stage_info["stage_type"], 
        actual_mode
    )
    
    # Get current points status
    current_status = get_current_points()
    new_total = current_status.get("total_points", 0) + stage_points
    
    # Check for bonus achievements
    bonus_points = calculator.check_bonus_eligibility({
        "stage_type": stage_info["stage_type"],
        "ride_mode": actual_mode,
        "stage_number": stage_info["stage_number"],
        "current_status": current_status
    })
    
    return {
        "stage_points": stage_points,
        "bonus_points": sum(bonus_points.values()),
        "new_total": new_total + sum(bonus_points.values()),
        "actual_mode": actual_mode,
        "bonuses_earned": bonus_points
    }

def generate_evening_summary(
    activity: Dict[str, Any],
    stage_info: Dict[str, Any], 
    points_result: Dict[str, Any]
) -> str:
    """Generate the evening points summary."""
    
    # Load mission config for context
    mission_cfg = bootstrap("missions/tdf_sim_2025.toml")
    
    # Initialize communication agent
    comm_agent = TDFCommunicationAgent()
    
    # Generate summary
    summary = comm_agent.generate_evening_summary(
        stage_results={
            "stage_number": stage_info["stage_number"],
            "stage_type": stage_info["stage_type"],
            "duration": stage_info["activity_duration"],
            "activity_id": activity["id"]
        },
        points_earned=points_result["stage_points"],
        total_points=points_result["new_total"],
        bonus_progress=points_result["bonuses_earned"]
    )
    
    return summary

def send_evening_notifications(summary: str):
    """Send evening summary via configured notification channels."""
    subject = "🎉 TDF Stage Complete - Points Summary"
    
    email_recipient = os.getenv("TO_EMAIL")
    sms_recipient = os.getenv("TO_PHONE")
    
    if email_recipient:
        send_email(subject, summary, email_recipient)
    
    if sms_recipient:
        send_sms(summary, sms_recipient, 
                use_twilio=os.getenv("USE_TWILIO", "false").lower() == "true")
    
    print("📧 Evening summary notifications sent")

def log_stage_completion(
    activity: Dict[str, Any],
    stage_info: Dict[str, Any], 
    points_result: Dict[str, Any]
):
    """Log stage completion to memory bus."""
    
    stage_data = {
        "date": stage_info["activity_date"].isoformat(),
        "stage_number": stage_info["stage_number"],
        "stage_type": stage_info["stage_type"],
        "actual_mode": points_result["actual_mode"],
        "stage_completed": True,
        "stage_points": points_result["stage_points"],
        "total_points": points_result["new_total"],
        "bonus_points_earned": points_result["bonus_points"],
        "activity_id": activity["id"],
        "workout_completed": True
    }
    
    log_tdf_stage(stage_data)
```

## Deployment Options

### Option 1: Webhook + Cloud Deployment

**Recommended for production use:**

```yaml
# docker-compose.yml
version: '3.8'
services:
  lanterne-webhook:
    build: .
    ports:
      - "5000:5000"
    environment:
      - STRAVA_CLIENT_ID=${STRAVA_CLIENT_ID}
      - STRAVA_CLIENT_SECRET=${STRAVA_CLIENT_SECRET}
      - STRAVA_WEBHOOK_SECRET=${STRAVA_WEBHOOK_SECRET}
      - WEBHOOK_CALLBACK_URL=${WEBHOOK_CALLBACK_URL}
    volumes:
      - ./memory:/app/memory
      - ./output:/app/output
```

**Setup process:**
1. Deploy webhook server to cloud (Heroku, Railway, DigitalOcean, etc.)
2. Register webhook with Strava using public URL
3. Configure environment variables
4. Test with sample activity

### Option 2: Polling + Local Deployment

**Good for development/personal use:**

```bash
# Terminal 1: Run the activity monitor
python scripts/run_activity_monitor.py

# Terminal 2: Continue with normal daily workflow
python scripts/daily_run.py
```

**Systemd service for Linux:**
```ini
# /etc/systemd/system/lanterne-activity-monitor.service
[Unit]
Description=Lanterne Rouge Activity Monitor
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/lanterne-rouge
ExecStart=/path/to/lanterne-rouge/.venv/bin/python scripts/run_activity_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Option 3: Hybrid Approach

**Best of both worlds:**
- Primary: Webhook for instant response
- Fallback: Polling every 15 minutes to catch missed events
- Manual trigger: Command to force evening workflow

```python
# Enhanced daily_run.py
def main():
    # Morning workflow (existing)
    morning_summary, _ = run_daily_logic()
    
    # Check for webhook server health
    if not webhook_server_healthy():
        # Start polling fallback
        start_polling_fallback()
    
    return morning_summary
```

## Configuration Updates

### Environment Variables
```env
# Webhook configuration
WEBHOOK_CALLBACK_URL=https://your-domain.com/webhook/strava
STRAVA_VERIFY_TOKEN=lanterne_rouge_2025
STRAVA_WEBHOOK_SECRET=your_secret_key
WEBHOOK_PORT=5000

# Activity monitoring
ACTIVITY_POLL_INTERVAL=300  # seconds
ENABLE_ACTIVITY_MONITOR=true

# Evening notifications
EVENING_NOTIFICATION_ENABLED=true
EVENING_EMAIL_SUBJECT="🎉 TDF Stage Complete"
```

### Mission Config Enhancement
```toml
# missions/tdf_sim_2025.toml
[tdf_simulation]
# ... existing config ...
activity_detection = "webhook"  # "webhook", "polling", "hybrid"
min_stage_duration = 30  # minutes
auto_mode_detection = true
manual_mode_override = false
```

## Benefits of Activity-Triggered Approach

1. **Immediate Feedback**: Get points summary within minutes of completing workout
2. **Real-time Motivation**: See progress immediately while motivation is high
3. **Accurate Tracking**: Capture actual workout completion vs. scheduled
4. **Better Engagement**: Timely feedback creates positive reinforcement loop
5. **Flexible Training**: Supports non-scheduled workouts and makeup sessions

## Implementation Priority

**Phase 1 (Week 1)**: 
- [ ] Build evening processor core logic
- [ ] Implement polling-based monitor for testing
- [ ] Test with manual activity detection

**Phase 2 (Week 2)**:
- [ ] Add webhook infrastructure
- [ ] Deploy webhook server
- [ ] Register with Strava API

**Phase 3 (Week 3)**:
- [ ] Enhance activity detection logic
- [ ] Add ride mode classification
- [ ] Improve evening summary templates

**Phase 4 (Week 4)**:
- [ ] Add hybrid fallback systems
- [ ] Performance optimization
- [ ] Production deployment

This approach transforms the TDF simulation from a scheduled notification system into a responsive, engaging experience that provides immediate feedback on your achievements!