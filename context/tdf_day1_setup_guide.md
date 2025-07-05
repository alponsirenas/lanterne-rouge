# 🏆 TDF Day 1 - Quick Setup Guide

## What You Get TODAY

✅ **Morning**: Ride mode recommendation (GC vs Breakaway) based on your readiness  
✅ **Evening**: Points summary after completing workouts  
✅ **Bonus tracking**: Progress toward 5 achievement bonuses  
✅ **Full integration**: Works with your existing Oura/Strava setup  

## 🚀 Quick Start (5 minutes)

### 1. Morning Workflow 
**Run BEFORE your workout:**

```bash
# Your existing morning routine
python scripts/daily_run.py

# NEW: Add TDF briefing
python scripts/morning_tdf_briefing.py
```

**This gives you:**
```
🏆 TDF Stage 1 - Flat Stage
==================================================

📊 READINESS CHECK:
• Readiness Score: 85/100
• TSB (Form): +2.3

🎯 TODAY'S RECOMMENDATION:
• Mode: BREAKAWAY
• Expected Points: 8
• Rationale: Aggressive approach for 8 points - good recovery state

🏆 BONUS OPPORTUNITIES:
   • 5 consecutive: 0/5
   • 10 breakaways: 0/10
   
🚴 GET OUT THERE AND CRUSH IT! 💪
```

### 2. Evening Workflow
**Run AFTER your workout (once uploaded to Strava):**

```bash
python scripts/evening_tdf_check.py
```

**This gives you:**
```
🎉 TDF Stage 1 Complete!

🏔️ Stage Type: Flat
🚴 Mode Completed: BREAKAWAY
⭐ Points Earned: +8

📊 Total Points: 8
📈 Stages Completed: 1/21

Tomorrow: Stage 2 (hilly)

Keep crushing it! 🚀
```

## 📋 Daily Routine (21 days)

### Every Morning:
1. Run: `python scripts/morning_tdf_briefing.py`
2. Check your ride mode recommendation 
3. Do your workout accordingly
4. Upload to Strava

### Every Evening:
1. Run: `python scripts/evening_tdf_check.py`
2. Get your points summary
3. See bonus progress
4. Get excited for tomorrow!

## 🎯 Stage Schedule

| Stage | Date | Type | GC Points | Breakaway Points |
|-------|------|------|-----------|------------------|
| 1 | Jul 5 | Flat | 5 | 8 |
| 2 | Jul 6 | Hilly | 7 | 11 |
| 3 | Jul 7 | Hilly | 7 | 11 |
| 4 | Jul 8 | Flat | 5 | 8 |
| 5 | Jul 9 | Hilly | 7 | 11 |
| 6 | Jul 10 | **Mountain** | 10 | **15** |
| ... | ... | ... | ... | ... |

## 🏆 Bonus Achievements

1. **5 Consecutive Stages**: +5 points (any 5 in a row)
2. **10 Breakaway Stages**: +15 points (total throughout event)
3. **All Mountains in Breakaway**: +10 points (stages 6,9,11,15,16,18)
4. **Complete Final Week**: +10 points (stages 16-21)
5. **All GC Mode**: +25 points (if you never go Breakaway)

## 🔧 Technical Notes

### Data Storage
- Points stored in: `output/tdf_points.json`
- Automatically created/updated
- Safe to edit manually if needed

### Ride Mode Detection
**Breakaway Mode** detected if:
- Suffer Score > 100, OR
- Duration > 60 minutes

**GC Mode** otherwise

### Safety Features
- Forces REST day if readiness < 60 or TSB < -20
- Prioritizes health over points
- Maintains existing Lanterne Rouge safety protocols

## 🐛 Troubleshooting

### "No activity found"
- Make sure activity is uploaded to Strava
- Check it's marked as "Ride" or "VirtualRide" 
- Wait a few minutes after upload, then retry

### "Not in TDF period"
- Scripts are configured for July 5-27, 2025
- Check system date is correct

### Missing notifications
- Check your `.env` file has `TO_EMAIL` and `TO_PHONE`
- Test with existing `daily_run.py` notifications

### Want to override ride mode?
Edit the evening script result or manually edit `output/tdf_points.json`

## 🚀 Tomorrow's Enhancements

After today, we can add:
- Auto-triggered evening workflow (no manual running)
- Webhook integration for instant feedback
- Enhanced ride mode detection
- Better integration with existing system

## 💪 Let's GO!

You're all set for Stage 1! The system will:

1. **Tell you what mode to ride** (based on your physiology)
2. **Track your points** (immediately after workouts)
3. **Motivate you** (with bonus progress and achievements)
4. **Keep you safe** (existing health monitoring intact)

**Today is Stage 1 (Flat): 5 points for GC mode, 8 points for Breakaway mode!**

Run the morning script now to get your recommendation! 🏆