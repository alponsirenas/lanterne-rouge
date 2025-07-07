# Lanterne Rouge v0.5.0 Release Notes

🏆 **Tour de France Points System Release**

## Overview

Version 0.5.0 introduces the **TDF Points System** - a gamified 21-stage Tour de France indoor simulation that transforms your training experience with ride mode recommendations, points tracking, and achievement bonuses.

## 🎯 Major Features

### TDF Points System
- **21-stage simulation** (July 5-27, 2025)
- **Dual ride modes**: GC (conservative) vs Breakaway (aggressive)
- **Dynamic points structure**: 5-15 points per stage based on type and mode
- **5 achievement bonuses**: Consecutive stages, breakaway count, mountain mastery, final week, consistency
- **Smart recommendations**: AI-powered mode selection based on readiness and TSB

### Automated Workflows
- **Morning briefings**: Ride mode recommendations with physiological analysis
- **Evening tracking**: Automatic points calculation when activities are logged
- **GitHub Actions integration**: 4 new workflows for complete automation
- **Intelligent notifications**: Email/SMS summaries with progress tracking

### New Scripts
- `scripts/morning_tdf_briefing.py` - Daily stage briefing and mode recommendation
- `scripts/evening_tdf_check.py` - Activity-triggered points calculation
- Enhanced notification system with TDF-specific messaging

## 🚀 Key Benefits

### For Athletes
- **Immediate feedback**: Points calculated within minutes of workout completion
- **Strategic guidance**: AI recommendations balance performance with recovery
- **Motivation boost**: Gamification with clear goals and achievements
- **Safety first**: Maintains existing health monitoring and rest day protocols

### For Coaches
- **Enhanced insights**: Detailed ride mode analysis and strategic recommendations
- **Automated tracking**: Complete points history and bonus progress
- **Flexible control**: Manual overrides and customizable parameters
- **Rich reporting**: Comprehensive summaries and trend analysis

## 🔧 Technical Enhancements

### GitHub Actions Workflows
- **Daily Coach + TDF Morning**: Combined morning briefing (7AM PT)
- **TDF Evening Check**: Automatic points tracking (multiple daily checks)
- **TDF Morning Briefing**: Standalone morning briefing
- **TDF Manual Check**: On-demand manual triggers with choice options

### Data Management
- **Points persistence**: JSON-based storage with automatic backups
- **Activity detection**: Smart classification of TDF stages vs regular training
- **Bonus tracking**: Real-time progress toward 5 achievement categories
- **Historical data**: Complete audit trail of all stages and decisions

### Integration Features
- **Existing system compatibility**: Works alongside current coaching system
- **Strava integration**: Automatic activity analysis and ride mode detection
- **Oura integration**: Physiological data drives mode recommendations
- **Notification system**: Leverages existing email/SMS infrastructure

## 🔋 Power-Based Analysis System (v0.5.0 Update)

### Scientific Training Load Assessment
- **Intensity Factor (IF)**: Normalized Power ÷ FTP for accurate relative effort assessment
- **Training Stress Score (TSS)**: Duration × IF² × 100 for quantified training load
- **Effort Level Classification**: Automatic power zone categorization (recovery/aerobic/tempo/threshold/vo2max/neuromuscular)
- **FTP Integration**: All calculations relative to athlete's Functional Threshold Power (128W)

### LLM-Powered Activity Analysis
- **Power-First Approach**: Prioritizes IF, TSS, and Normalized Power over subjective metrics
- **Intelligent Context Analysis**: LLM evaluates power metrics with stage type and strategic considerations
- **Confidence Scoring**: AI provides confidence levels and performance indicators
- **Enhanced Validation**: Comprehensive input validation and sanitization for all LLM interactions

### Smart Ride Mode Classification
**Breakaway Mode (Aggressive)**:
- IF ≥ 0.85 (Zone 4+ effort)
- TSS ≥ 60 (High training load)
- Strategy: High-intensity effort pushing physiological limits

**GC Mode (Conservative)**:
- IF ≥ 0.70 (Zone 3+ effort)
- TSS ≥ 40 (Moderate training load)
- Strategy: Sustainable effort focused on consistent completion

**Rest Mode (Recovery)**:
- IF < 0.70 (Zone 1-2 effort)
- TSS < 40 (Low training load)
- Strategy: Active recovery or very easy effort

### Post-Stage LLM Evaluation
- **Comprehensive Analysis**: Strategic performance evaluation with recovery recommendations
- **Campaign Strategy**: Advice for upcoming stages considering current fitness state
- **Personalized Motivation**: Encouraging, context-aware communication
- **Training Load Management**: TSS-based recovery guidance and strategic planning

### Enhanced Fallback System
- **Rule-Based Power Analysis**: When LLM unavailable, uses power-based classification rules
- **Graceful Degradation**: Maintains scientific accuracy even without LLM
- **Suffer Score Fallback**: Only used when power data is insufficient
- **Robust Error Handling**: Comprehensive error catching with detailed logging

### Configuration Enhancements
```toml
# Power-based thresholds in missions/tdf_sim_2025.toml
[athlete]
ftp = 128  # Functional Threshold Power for all calculations

[tdf_simulation.detection]
breakaway_intensity_threshold = 0.85  # IF for breakaway classification
breakaway_tss_threshold = 60          # TSS for breakaway classification
gc_intensity_threshold = 0.70         # IF for GC classification
gc_tss_threshold = 40                 # TSS for GC classification
fallback_suffer_threshold = 100       # Fallback when power unavailable
```

### Technical Implementation
- **Power Metrics Calculation**: New `calculate_power_metrics()` function in validation.py
- **Enhanced Activity Analysis**: Updated `analyze_activity_with_llm()` with power-first approach
- **Validation Layer**: Comprehensive input validation and sanitization
- **LLM Integration**: Seamless integration with existing AI client infrastructure

## 📊 Points Structure

| Stage Type | GC Mode | Breakaway Mode |
|------------|---------|----------------|
| Flat | 5 pts | 8 pts |
| Hilly | 7 pts | 11 pts |
| Mountain | 10 pts | 15 pts |
| ITT | 4 pts | 6 pts |
| Mountain ITT | 6 pts | 9 pts |

## 🏆 Achievement Bonuses

1. **5 Consecutive Stages**: +5 points
2. **10+ Breakaway Stages**: +15 points
3. **All Mountains in Breakaway**: +10 points
4. **Complete Final Week**: +10 points
5. **All GC Mode**: +25 points

## 🎮 User Experience

### Morning Workflow
```
🏆 TDF Stage 1 - Flat Stage
📊 READINESS: 85/100, TSB: +2.3
🎯 RECOMMEND: BREAKAWAY (8 points)
🏆 BONUS: 0/5 consecutive stages
```

### Evening Workflow
```
🎉 TDF Stage 1 Complete!
🚴 Mode: BREAKAWAY (+8 points)
📊 Total: 8 points (1/21 stages)
Tomorrow: Stage 2 (hilly)
```

## 🔄 Backwards Compatibility

- **Existing coaching system**: Unchanged and fully functional
- **Current workflows**: Continue to work as before
- **Data integrity**: All existing data preserved
- **API compatibility**: No breaking changes to existing interfaces

## 📱 Setup and Usage

### Quick Start
1. Enable new GitHub Actions workflows
2. Run morning briefing: `python scripts/morning_tdf_briefing.py`
3. Complete workout based on recommendation
4. Run evening check: `python scripts/evening_tdf_check.py`

### Automated Experience
- **7AM PT**: Automatic morning briefing
- **Throughout day**: Automatic evening checks (3PM, 6PM, 9PM, 11PM PT)
- **Manual triggers**: Available anytime via GitHub Actions

## 🐛 Bug Fixes

- Fixed YAML linting issues in workflow files
- Improved error handling in activity detection
- Enhanced notification reliability
- Better timezone handling for scheduled workflows

## 📚 Documentation

### New Documentation
- `context/tdf_coaching_evaluation_plan.md` - Comprehensive coaching plan
- `context/tdf_technical_implementation_plan.md` - Technical implementation guide
- `context/tdf_day1_setup_guide.md` - Quick setup guide
- `context/tdf_github_actions_setup.md` - Automation setup guide
- `context/tdf_activity_triggered_workflow.md` - Advanced workflow design

### Updated Documentation
- Enhanced README with TDF system overview
- Updated context files with new feature descriptions
- Improved setup instructions and troubleshooting guides

## 🚀 What's Next

### Immediate (July 2025)
- TDF simulation execution and monitoring
- Real-time system performance optimization
- User feedback collection and iteration

### Future Enhancements
- Webhook integration for instant activity processing
- Advanced ride mode detection algorithms
- Enhanced bonus achievement system
- Mobile app integration possibilities

## 🎉 Getting Started

The TDF Points System is ready for immediate use! Enable the GitHub Actions workflows and start your 21-stage simulation journey. The system provides everything needed for a complete, automated, and engaging Tour de France experience.

**Ready to start your TDF simulation? Enable the workflows and run your first morning briefing!** 🏆

---

*This release maintains full backwards compatibility while adding powerful new gamification features. The existing Lanterne Rouge coaching system continues to work exactly as before, with the TDF system as an optional enhancement.*