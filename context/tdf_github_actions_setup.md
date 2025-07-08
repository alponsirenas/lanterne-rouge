# 🤖 TDF GitHub Actions Setup

## Overview

I've created **4 GitHub Actions workflows** that automate your entire TDF experience:

1. **🌅 Daily Coach** - Regular daily coaching with TDF-aware recommendations (7AM PT)
2. **🎉 TDF Evening Check** - Automatic evening points tracking (multiple times daily)  
3. **🌅 TDF Morning Briefing** - Standalone morning TDF briefing (6AM PT)
4. **⚡ TDF Manual Check** - On-demand manual triggers

## 🚀 Quick Setup (2 minutes)

### 1. Commit the New Workflows
```bash
# Add the workflow files (already committed)
git add .github/workflows/tdf-*.yml
git add .github/workflows/daily.yml
git commit -m "feat: add TDF GitHub Actions workflows"
git push
```

### 2. Enable Workflows
1. Go to your GitHub repo → **Actions** tab
2. You'll see the workflows listed
3. Click **"Enable workflow"** for each one

### 3. Test Immediately
**Run the manual check right now:**
1. Go to **Actions** → **TDF Manual Stage Check**
2. Click **"Run workflow"**
3. Select **"morning"** to get today's briefing
4. Click **"Run workflow"**

## 📅 Automatic Schedule

### Morning Briefings
- **Daily Coach** (7AM PT / 14:00 UTC) - Regular coaching + TDF context when active
- **TDF Morning Briefing** (6AM PT / 13:00 UTC) - TDF-specific stage recommendations (July only)

### Evening Points Tracking (PT timezone)
- **3PM PT (22:00 UTC)** - Early afternoon check
- **6PM PT (01:00 UTC)** - Evening workout check  
- **9PM PT (04:00 UTC)** - Late workout check
- **11PM PT (06:00 UTC)** - Final daily check

Each run checks for new Strava activities and calculates points if found.

## 🎯 What Each Workflow Does

### 🌅 Daily Coach
**Runs:** Every day at 7AM PT  
**Sends you:**
```
Subject: Daily Training Plan

[Regular Lanterne Rouge coaching with TDF context when active]

🏆 TDF Stage 1 - Flat Stage (when TDF active)
📊 READINESS: 85/100, TSB: +2.3  
🎯 STAGE STRATEGY: Recommendations based on current points
```

### 🌅 TDF Morning Briefing
**Runs:** Every day at 6AM PT during July  
**Sends you:**
```
Subject: TDF Stage Briefing and Recommendations

🏆 TDF Stage 1 - Flat Stage
📊 READINESS: 85/100, TSB: +2.3
🎯 RECOMMEND: BREAKAWAY (8 points)
🏆 BONUS PROGRESS: 0/5 consecutive
💪 STRATEGY: Power-based analysis and stage insights
```

### 🎉 TDF Evening Check  
**Runs:** 4 times daily during typical workout hours  
**Sends you:** (only when new stage completed)
```
Subject: 🎉 TDF Stage Complete - Points Summary

🎉 TDF Stage 1 Complete!
🚴 Mode: BREAKAWAY (+8 points)
📊 Total: 8 points (1/21 stages)
🔥 Power Analysis: IF 0.87, TSS 85
Tomorrow: Stage 2 (hilly)
```

### ⚡ TDF Manual Check
**Runs:** When you trigger it manually  
**Use cases:**
- Just finished a workout? Trigger "evening" check
- Want your briefing again? Trigger "morning" check  
- Testing? Trigger "both"

## 🔧 Advanced Configuration

### Customize Timing
Edit the `cron` schedules in the workflow files:
```yaml
schedule:
  - cron: '0 14 * 7 *'  # 7AM PT = 14:00 UTC (daily.yml)
  - cron: '0 13 * 7 *'  # 6AM PT = 13:00 UTC (tdf-morning.yml)
```

### Change Notifications
All workflows use your existing notification setup:
- `TO_EMAIL` for email notifications
- `TO_PHONE` for SMS notifications
- Uses `GH_PAT` for protected branch access

### July-Only Execution
TDF-specific workflows run only in July (`* 7 *`). The daily coach runs year-round but includes TDF context when active.

## 🎮 Usage During TDF

### Daily Routine:
1. **7AM**: Get automatic morning briefing (email/SMS)
2. **Do your workout** based on recommendation
3. **Upload to Strava**
4. **Wait 5-30 minutes**: Automatic points calculation
5. **Get points notification** (email/SMS)

### Manual Triggers:
- **Just finished workout?** Run "TDF Manual Check" → "evening"
- **Want immediate briefing?** Run "TDF Manual Check" → "morning"  
- **Testing?** Run "TDF Manual Check" → "both"

## 📊 Data Tracking

### Automatic Commits
- Points data saved to `output/tdf_points.json`
- Automatically committed to your repo
- Creates pull requests for major updates
- Full history tracking

### GitHub Actions Summary
Each run shows:
- ✅ Stage completed status
- 📊 Points earned
- 🏆 Bonus progress
- 📈 Current standings

## 🐛 Troubleshooting

### Workflows Not Running?
1. Check **Actions** tab → **Enable workflows**
2. Verify it's July (workflows are July-only)
3. Check your secrets are still valid

### No Notifications?
1. Verify `TO_EMAIL` and `TO_PHONE` secrets
2. Test with existing `daily.yml` workflow
3. Check spam/junk folders

### Points Not Updating?
1. Ensure Strava activity is uploaded
2. Check it's marked as "Ride" or "VirtualRide"
3. Run manual evening check to test

### Want to Stop Automation?
Disable workflows in GitHub Actions tab (keeps manual triggers available).

## 🚀 Ready to Go!

**Your automated TDF experience:**

✅ **7AM Daily**: Automatic morning briefing with ride mode recommendation  
✅ **Throughout day**: Automatic evening checks (3PM, 6PM, 9PM, 11PM PT)  
✅ **Instant feedback**: Points calculated within 30 minutes of Strava upload  
✅ **Manual control**: Run checks anytime via GitHub Actions  
✅ **Full history**: All data tracked and committed automatically  

**Go enable the workflows and test the manual check right now!** 🏆