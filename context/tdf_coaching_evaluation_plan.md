# Tour de France Indoor Simulation 2025 — Coaching and Evaluation Plan

## Event Overview

**Event**: Tour de France Indoor Simulation 2025  
**Duration**: July 5 – July 27, 2025 (3 weeks)  
**Mission ID**: `tdf-sim-2025`  
**Objective**: Complete a full 3-week simulated Tour experience with intelligent fatigue management, climbing stages, and threshold efforts while maintaining athlete health and motivation.

## Mission Parameters

- **CTL Peak Target**: 55 (sustainable completion focus)
- **Long Ride Cap**: 75 minutes maximum
- **Stage Climb Duration**: 60 minutes
- **Threshold Intervals**: 20 minutes minimum
- **Athlete FTP**: 128 watts
- **Minimum Readiness**: 70
- **Minimum TSB**: -15 (fatigue management threshold)

## Points System & Daily Ride Modes

### Daily Ride Mode Options
**GC Mode (Conservative)**: Focus on consistent completion, lower risk
**Breakaway Mode (Aggressive)**: Higher intensity for bonus points, higher risk

### Points Structure
| Stage Type   | GC Mode (Base) | Breakaway Mode (Total) |
|--------------|----------------|-------------------------|
| Flat         | 5 pts          | 8 pts (5+3 bonus)      |
| Hilly        | 7 pts          | 11 pts (7+4 bonus)     |
| Mountain     | 10 pts         | 15 pts (10+5 bonus)    |
| ITT          | 4 pts          | 6 pts (4+2 bonus)      |
| Mountain ITT | 6 pts          | 9 pts (6+3 bonus)      |

### Completion Bonuses
- Complete all GC Mode stages: +25 points
- Complete 10+ Breakaway stages: +15 points  
- Complete 5 consecutive stages: +5 points
- Complete all mountain stages in Breakaway Mode: +10 points
- Complete final week (Stages 16-21): +10 points

### Daily Workflow
**Morning**: AI recommends ride mode based on readiness, TSB, and fatigue state  
**Evening**: Calculate points earned, update total, track bonus progress

## Phase 1: Pre-Event Preparation (Today - July 4, 2025)

### Immediate Assessment (Days 1-3)
- **Daily coaching review** via `daily_run.py` execution
- **Baseline measurement** of current CTL, ATL, TSB values
- **Readiness calibration** using Oura Ring data
- **System validation** ensuring all AI agents are operational

### Final Preparation (Days 4-7)
- **Taper protocol** to optimize TSB for event start
- **Equipment check** for simulation setup
- **Mission config validation** ensuring parameters align with athlete capacity
- **Communication testing** for daily coaching delivery

## Phase 2: Simulation Event Execution (July 5-27, 2025)

### Daily Coaching Protocol

#### Morning Assessment (6:00-8:00 AM)
1. **Automated data collection**:
   - Oura Ring readiness score and contributors
   - Previous day's Strava activity data
   - CTL/ATL/TSB calculation via Bannister model

2. **AI-powered decision making**:
   - Reasoning Agent evaluates readiness vs. mission demands
   - Decision output: PUSH, EASE, or RECOVER
   - Rationale based on TSB, readiness score, and stage requirements

3. **Coaching communication**:
   - LLM-generated daily summary in first-person, conversational tone
   - **Recommended ride mode**: GC Mode vs. Breakaway Mode based on readiness/fatigue
   - Specific workout prescription with time-in-zone guidance
   - Points opportunity and strategic context for the day's focus

#### Ride Mode Selection Strategy

**GC Mode** (Conservative, Consistent):
- **When to recommend**: TSB < -10, readiness < 75, consecutive high-load days
- **Focus**: Stage completion, CTL maintenance, fatigue management
- **Risk level**: Low - prioritizes finishing over performance
- **Points**: Base points only (5-10 per stage depending on type)

**Breakaway Mode** (Aggressive, High Reward):
- **When to recommend**: TSB > -5, readiness > 80, fresh from rest day
- **Focus**: Performance gains, bonus points, tactical opportunities
- **Risk level**: Higher - increased intensity for greater reward
- **Points**: Base + bonus points (8-15 per stage depending on type)

#### Stage Categories and Coaching Approach

**Mountain Stages** (8-10 stages expected):
- **GC Mode**: Zone 3 sustained efforts, 60-minute duration (10 pts)
- **Breakaway Mode**: Zone 3-4 with surges, KOM efforts (15 pts)
- **Coaching focus**: Pacing strategy, fatigue tolerance, mental resilience
- **Key metrics**: Power consistency, heart rate drift, perceived exertion

**Hilly Stages** (8-10 stages expected):
- **GC Mode**: Zone 2-3 rolling efforts, up to 75 minutes (7 pts)
- **Breakaway Mode**: Zone 3-4 with punchy climbs, sprint efforts (11 pts)
- **Coaching focus**: Power variability, tactical positioning
- **Key metrics**: Power spikes, recovery between efforts

**Flat Stages** (3-5 stages expected):
- **GC Mode**: Zone 2 steady efforts, endurance focus (5 pts)
- **Breakaway Mode**: Zone 2-4 with sprint intervals (8 pts)
- **Coaching focus**: Aerobic efficiency, sprint power development
- **Key metrics**: Sustained power, sprint peak output

**Time Trial Stages** (2-3 stages expected):
- **Individual TT**: GC Mode 4 pts, Breakaway Mode 6 pts
- **Mountain TT**: GC Mode 6 pts, Breakaway Mode 9 pts
- **Coaching focus**: Pacing precision, threshold power maintenance
- **Key metrics**: Power consistency, aerodynamic efficiency

#### Evening Review (8:00-10:00 PM)
1. **Performance analysis**:
   - Workout completion assessment
   - **Stage points calculation**: Mode completed + bonus eligibility
   - **Total points update**: Running total with bonus tracking
   - Data quality validation
   - Fatigue accumulation tracking

2. **Points summary**:
   - Points earned today (base + any bonuses)
   - Current total points
   - Progress toward bonus thresholds (consecutive stages, mode-specific achievements)
   - Strategic recommendations for upcoming stages

3. **Plan adaptation**:
   - Next-day preparation based on current state
   - Next-day ride mode pre-assessment
   - Weekly trend analysis
   - Mission progress evaluation

### Weekly Coaching Cycles

#### Week 1 (July 5-11): Foundation
- **Objective**: Establish rhythm and assess adaptation
- **Focus**: Conservative progression, system calibration
- **Key stages**: 2-3 climbing stages, 4-5 endurance stages
- **Recovery**: Built-in rest day if TSB drops below -10

#### Week 2 (July 12-18): Peak Demand
- **Objective**: Maximum simulation load
- **Focus**: Back-to-back stage management, cumulative fatigue tolerance
- **Key stages**: 3-4 climbing stages, 2 threshold stages, 2-3 endurance stages
- **Recovery**: Strategic recovery insertion based on readiness scores

#### Week 3 (July 19-27): Resilience and Completion
- **Objective**: Maintain quality under accumulated fatigue
- **Focus**: Mental fortitude, completion over performance
- **Key stages**: 2-3 climbing stages, final threshold efforts
- **Recovery**: Aggressive recovery protocol to ensure completion

## Phase 3: Evaluation Framework

### Daily Evaluation Metrics

**Physiological Markers**:
- CTL progression (target: maintain 45-55 range)
- ATL management (avoid sustained >65)
- TSB balance (keep above -15)
- Readiness score trends (maintain >70 average)
- Resting heart rate stability (<56)

**Performance Indicators**:
- Stage completion rate (target: 100%)
- **Points earned per stage**: Track daily points and mode selection
- **Total points accumulation**: Running total with bonus tracking
- **Ride mode accuracy**: How often AI recommendations align with optimal choices
- Power consistency within prescribed zones
- Heart rate response stability
- Perceived exertion alignment with prescribed intensity

**Psychological Markers**:
- Daily motivation scores (self-reported 1-10)
- Stress indicators from Oura data
- Sleep quality maintenance
- Communication engagement with coaching prompts

### Weekly Evaluation Protocol

**Monday Assessment**:
- Previous week's data compilation
- Trend analysis via memory bus system
- Plan adaptation recommendations
- Agent performance review

**Wednesday Check-in**:
- Mid-week fatigue assessment
- Readiness score correlation analysis
- Workout prescription accuracy review
- Recovery protocol effectiveness

**Friday Planning**:
- Weekend stage preparation
- Weekly objective setting
- Risk assessment for upcoming demands
- Contingency planning for low readiness days

### Agent Performance Evaluation

#### Tour Coach Agent
- **Quality of daily summaries**: Clarity, motivation, actionability
- **Prediction accuracy**: Readiness vs. actual performance correlation
- **Adaptation speed**: Response time to changing conditions
- **Communication effectiveness**: Athlete engagement and compliance

#### Reasoning Agent
- **Decision consistency**: Logical alignment with mission parameters
- **Risk management**: Protection against overreaching
- **Goal optimization**: Balance between challenge and completion
- **Learning capability**: Improvement over the 3-week period

#### Monitor Agent
- **Data accuracy**: Reliable capture of Oura and Strava metrics
- **Calculation precision**: Bannister model implementation correctness
- **Integration reliability**: Consistent API connections
- **Alert responsiveness**: Timely flagging of concerning trends

## Success Criteria

### Primary Objectives (Mission Critical)
1. **Event completion**: 100% of planned simulation stages
2. **Health maintenance**: No injury, illness, or severe overreaching
3. **CTL preservation**: Maintain CTL >50 throughout event
4. **System reliability**: <5% downtime in AI coaching system

### Secondary Objectives (Performance Optimization)
1. **Quality completion**: >80% of stages completed at prescribed intensity
2. **Points optimization**: Achieve >150 total points (average ~7 points per stage)
3. **Strategic ride mode selection**: AI recommendations lead to optimal points/risk balance
4. **Readiness management**: Average readiness score >75
5. **Recovery efficiency**: TSB recovery to positive values within 48 hours of rest days
6. **Adaptation demonstration**: Improved power output or efficiency by week 3

### Tertiary Objectives (System Learning)
1. **AI coaching refinement**: Documented improvements in decision-making accuracy
2. **Bonus achievement targets**: Earn at least 2 of the 5 possible completion bonuses
3. **Data insights**: New correlations between readiness metrics and performance
4. **Protocol optimization**: Refined coaching strategies for future events
5. **User experience enhancement**: Improved communication and engagement patterns

### Bonus Achievement Strategy
- **5 consecutive stages bonus** (+5 pts): Target early in Week 1 when fresh
- **10+ Breakaway stages bonus** (+15 pts): Balanced throughout event based on readiness
- **All mountain stages in Breakaway mode** (+10 pts): Aggressive strategy when conditions allow
- **Final week completion** (+10 pts): Conservative approach to ensure finishing
- **All GC Mode stages** (+25 pts): Fallback strategy if health/fatigue demands conservative approach

## Risk Management

### High-Risk Scenarios

**Overreaching/Overtraining**:
- **Indicators**: TSB <-20, readiness <60 for 3+ days, elevated RHR
- **Response**: Immediate rest day insertion, medical consultation if needed
- **Prevention**: Conservative progression, mandatory rest day triggers

**Technology Failure**:
- **Indicators**: API failures, data collection gaps, AI system downtime
- **Response**: Manual coaching backup, simplified decision tree protocols
- **Prevention**: System redundancy, daily health checks, backup data sources

**Motivation/Compliance Issues**:
- **Indicators**: Skipped workouts, poor engagement with coaching
- **Response**: Personalized communication, goal adjustment, social support
- **Prevention**: Engaging communication style, achievable daily targets

**External Life Stress**:
- **Indicators**: Sleep disruption, schedule conflicts, family/work demands
- **Response**: Flexible scheduling, reduced intensity, stress management support
- **Prevention**: Contingency planning, communication of life priorities

### Mitigation Strategies

1. **Daily decision trees** with clear escalation protocols
2. **Multiple fallback positions** for each week's objectives
3. **Human oversight integration** for critical decisions
4. **Flexible mission parameter adjustment** within safety boundaries

## Communication Protocols

### Daily Communication
- **Morning coaching summary**: Delivered via configured notification system
- **Workout prescription**: Specific, actionable instructions
- **Motivation messaging**: Contextual encouragement and perspective
- **Progress updates**: Brief status on mission objectives

### Weekly Communication
- **Comprehensive review**: Data trends, achievements, challenges
- **Upcoming focus**: Next week's primary objectives and stage previews
- **System performance**: AI agent effectiveness and any adjustments made
- **Motivation and context**: Connection to larger mission goals

### Emergency Communication
- **Immediate alerts**: For concerning health metrics or system failures
- **Escalation procedures**: When human intervention is required
- **Recovery protocols**: Detailed instructions for rest and adaptation

## Technology Stack Monitoring

### Daily System Health Checks
- API connectivity (Oura, Strava, OpenAI)
- Database integrity (`memory/lanterne.db`)
- Agent execution success rates
- Data quality validation
- **Points calculation accuracy**: Verify daily scoring matches stage type and mode
- **Bonus tracking integrity**: Ensure consecutive stage counts and achievement flags are accurate

### Performance Optimization
- LLM response quality assessment
- Decision-making latency monitoring
- Memory system efficiency
- User interface responsiveness
- **Ride mode recommendation accuracy**: Track success rate of AI mode suggestions

### Required Technology Enhancements

**Points Tracking System**:
- Add `stage_points` and `total_points` fields to daily observations
- Track `ride_mode_selected` (GC/Breakaway) and `stage_type` in memory bus
- Implement bonus tracking: consecutive stages, mode-specific achievements
- Create points calculation logic based on stage completion and mode

**Enhanced AI Decision Making**:
- Extend reasoning module to include ride mode recommendations
- Factor in points strategy (conservative vs. aggressive) based on current standings
- Include bonus opportunity assessment in daily recommendations

**User Interface Updates**:
- Morning coaching: Display recommended ride mode with rationale
- Evening summary: Show points earned, total points, bonus progress
- Weekly dashboard: Points trends, mode selection patterns, strategic insights

**Database Schema Extensions**:
```sql
-- Add to daily observations table
stage_type VARCHAR(20),           -- 'flat', 'hilly', 'mountain', 'itt', 'mtn_itt'
ride_mode VARCHAR(20),            -- 'gc', 'breakaway'
stage_points INTEGER,             -- Points earned this stage
total_points INTEGER,             -- Running total
consecutive_stages INTEGER,       -- Count for bonus tracking
breakaway_stages_completed INTEGER -- Count for bonus tracking
```

## Post-Event Analysis Plan

### Immediate Post-Event (July 28-31)
- Complete data export and backup
- Initial performance analysis
- Health status assessment
- System performance review

### 30-Day Follow-up (August)
- Adaptation outcomes analysis
- Long-term fitness impact assessment
- AI coaching effectiveness study
- Recommendations for future events

### Lessons Learned Documentation
- Technical improvements needed
- Coaching strategy refinements
- Mission parameter calibration
- User experience enhancements

## Conclusion

This coaching and evaluation plan provides a comprehensive framework for successfully completing the Tour de France Indoor Simulation 2025 while maintaining athlete health, optimizing AI system performance, and generating valuable insights for future development. The plan balances ambitious event completion goals with conservative health management, ensuring the "Lanterne Rouge" philosophy of finishing strong rather than burning out.

The success of this simulation will validate the Lanterne Rouge system's ability to provide intelligent, adaptive coaching for complex endurance challenges while maintaining transparency, safety, and motivation throughout the journey.