# TDF Points System Implementation Plan - v0.5.0 Update

## ✅ COMPLETED: Power-Based Activity Analysis System

### Power-Based Analysis Features ✅

#### 1. Scientific Training Load Assessment
- **Intensity Factor (IF)**: Normalized Power ÷ FTP for accurate effort assessment
- **Training Stress Score (TSS)**: Duration × IF² × 100 for training load quantification
- **Effort Level Classification**: Automatic categorization (recovery/aerobic/tempo/threshold/vo2max/neuromuscular)
- **Normalized Power Integration**: Uses weighted average power for variability compensation

#### 2. LLM-Powered Activity Analysis ✅
- **Intelligent Stage Mode Detection**: LLM analyzes power metrics to determine GC/Breakaway/Rest modes
- **Power-First Analysis**: Prioritizes IF, TSS, and NP over subjective metrics like suffer score
- **Contextual Reasoning**: Considers stage type, athlete FTP, and training thresholds
- **Confidence Scoring**: LLM provides confidence levels and performance indicators

#### 3. Enhanced Detection Thresholds ✅
```toml
# Power-based thresholds (missions/tdf_sim_2025.toml)
[tdf_simulation.detection]
min_stage_duration_minutes = 30
breakaway_intensity_threshold = 0.85  # IF threshold for breakaway effort
breakaway_tss_threshold = 60          # TSS threshold for breakaway effort
gc_intensity_threshold = 0.70         # IF threshold for solid GC effort
gc_tss_threshold = 40                 # TSS threshold for GC effort
fallback_suffer_threshold = 100       # Fallback when power unavailable
```

#### 4. Robust Fallback System ✅
- **Rule-Based Power Analysis**: When LLM unavailable, uses power-based rules
- **Suffer Score Fallback**: Only used when power data is insufficient
- **Input Validation**: Comprehensive validation and sanitization of all inputs
- **Error Handling**: Graceful degradation with detailed logging

#### 5. Post-Stage LLM Evaluation ✅
- **Strategic Performance Analysis**: LLM provides comprehensive post-stage evaluation
- **Recovery Recommendations**: Personalized recovery advice based on training load
- **Campaign Strategy**: Strategic guidance for upcoming stages
- **Motivational Messaging**: Encouraging, personalized communication

### Technical Architecture ✅

#### Power Metrics Calculation
```python
def calculate_power_metrics(activity_data: Dict[str, Any], ftp: int) -> Dict[str, Any]:
    """Calculate power-based training metrics using athlete's FTP."""
    intensity_factor = normalized_power / ftp
    tss = duration_hours * (intensity_factor ** 2) * 100
    effort_level = classify_effort_level(intensity_factor)
    return {
        'intensity_factor': intensity_factor,
        'tss': tss,
        'normalized_power': normalized_power,
        'effort_level': effort_level
    }
```

#### LLM Integration Points
- **Activity Analysis**: `analyze_activity_with_llm()` in `scripts/evening_tdf_check.py`
- **Stage Evaluation**: `generate_llm_stage_evaluation()` for post-stage analysis
- **Validation Layer**: `src/lanterne_rouge/validation.py` for input sanitization
- **Power Metrics**: Integration with athlete FTP from mission configuration

### Configuration Integration ✅

#### Mission Configuration
```toml
[athlete]
ftp = 128  # Functional Threshold Power in watts

[tdf_simulation.detection]
# Science-based thresholds using power zones
breakaway_intensity_threshold = 0.85  # Zone 4+ effort
gc_intensity_threshold = 0.70         # Zone 3+ effort
```

#### Environment Variables
```bash
USE_LLM_REASONING=true
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4-turbo-preview
```

---

## ORIGINAL IMPLEMENTATION PLAN

# TDF Points System Implementation Plan

## Current Architecture Analysis

### Core Components
- **Entry Point**: `scripts/daily_run.py` - orchestrates daily execution
- **TourCoach**: Main orchestrator coordinating 3 agents
- **ReasoningAgent**: Makes training decisions (recover/ease/maintain/push) 
- **WorkoutPlanner**: Generates structured workouts based on decisions
- **CommunicationAgent**: Creates natural language summaries
- **Memory System**: SQLite database (`memory/lanterne.db`) for persistence
- **Mission Config**: TOML-based configuration with athlete parameters

### Current Data Flow
1. `daily_run.py` loads mission config and gets metrics (readiness, CTL, ATL, TSB)
2. `TourCoach.generate_daily_recommendation()` orchestrates:
   - `ReasoningAgent.make_decision()` → TrainingDecision
   - `WorkoutPlanner.generate_workout()` → WorkoutPlan  
   - `CommunicationAgent.generate_summary()` → formatted summary
3. Results logged to memory bus and sent via notifications

## Implementation Plan

### Phase 1: Database Schema Extensions

#### 1.1 Update Memory Database Schema
**File**: `src/lanterne_rouge/memory_bus.py`

```sql
-- Add new table for TDF simulation tracking
CREATE TABLE IF NOT EXISTS tdf_simulation (
    date TEXT PRIMARY KEY,
    stage_number INTEGER,
    stage_type TEXT,              -- 'flat', 'hilly', 'mountain', 'itt', 'mtn_itt'
    recommended_mode TEXT,        -- 'gc', 'breakaway'
    actual_mode TEXT,             -- 'gc', 'breakaway', 'rest'
    stage_completed BOOLEAN,
    stage_points INTEGER,
    total_points INTEGER,
    consecutive_stages INTEGER,
    breakaway_stages_completed INTEGER,
    bonus_points_earned INTEGER,
    workout_completed BOOLEAN,
    notes TEXT
);

-- Add stage scheduling table
CREATE TABLE IF NOT EXISTS stage_schedule (
    stage_number INTEGER PRIMARY KEY,
    date TEXT,
    stage_type TEXT,
    stage_name TEXT,
    description TEXT
);

-- Extend existing memory table for ride mode context
ALTER TABLE memory ADD COLUMN ride_mode_data TEXT DEFAULT NULL;
```

#### 1.2 Add Points Tracking Functions
**New functions in memory_bus.py**:

```python
def log_tdf_stage(stage_data: Dict[str, Any]) -> None:
    """Log TDF stage completion data."""
    
def get_current_points() -> Dict[str, Any]:
    """Get current points status and bonus progress."""
    
def get_stage_schedule() -> List[Dict[str, Any]]:
    """Get the complete 21-stage schedule."""
    
def initialize_stage_schedule() -> None:
    """Initialize the 21-stage TDF simulation schedule."""
```

### Phase 2: Ride Mode Decision System

#### 2.1 Extend ReasoningAgent
**File**: `src/lanterne_rouge/reasoner.py`

```python
@dataclass
class TDFDecision:
    """Extended decision structure for TDF simulation."""
    # Existing TrainingDecision fields
    action: str
    reason: str  
    intensity_recommendation: str
    flags: List[str]
    confidence: float
    
    # New TDF-specific fields
    recommended_ride_mode: str  # 'gc', 'breakaway', 'rest'
    mode_rationale: str
    stage_type: str
    expected_points: int
    bonus_opportunities: List[str]
    strategic_notes: str

class TDFReasoningAgent(ReasoningAgent):
    """Extended reasoning agent for TDF simulation."""
    
    def make_tdf_decision(
        self, 
        metrics: Dict[str, Any], 
        mission_config: MissionConfig,
        current_date: date,
        stage_info: Dict[str, Any],
        points_status: Dict[str, Any]
    ) -> TDFDecision:
        """Make TDF-specific decision including ride mode recommendation."""
```

#### 2.2 Ride Mode Selection Logic

**Rules for Mode Recommendation**:
```python
def _recommend_ride_mode(self, metrics: Dict, stage_type: str, points_status: Dict) -> tuple[str, str]:
    """Recommend ride mode based on current state."""
    readiness = metrics.get('readiness_score', 75)
    tsb = metrics.get('tsb', 0)
    consecutive = points_status.get('consecutive_stages', 0)
    breakaway_count = points_status.get('breakaway_stages_completed', 0)
    
    # Force rest day logic
    if readiness < 60 or tsb < -20:
        return 'rest', 'Recovery needed - metrics indicate overreaching risk'
    
    # Conservative GC mode conditions
    if (readiness < 75 or tsb < -10 or 
        metrics.get('consecutive_high_days', 0) >= 2):
        base_points = self._get_base_points(stage_type)
        return 'gc', f'Conservative approach for {base_points} base points - preserving energy'
    
    # Aggressive Breakaway mode conditions  
    if (readiness > 80 and tsb > -5 and 
        consecutive < 5):  # Opportunity for consecutive bonus
        total_points = self._get_total_points(stage_type)
        return 'breakaway', f'Aggressive approach for {total_points} total points - good recovery state'
        
    # Balanced decision based on stage type and current standings
    return self._balanced_mode_selection(stage_type, points_status)
```

### Phase 3: Stage Scheduling System

#### 3.1 Create Stage Calendar
**New file**: `src/lanterne_rouge/stage_calendar.py`

```python
from datetime import date, timedelta
from typing import List, Dict

STAGE_TYPES = {
    1: 'flat', 2: 'hilly', 3: 'hilly', 4: 'flat', 5: 'hilly',
    6: 'mountain', 7: 'flat', 8: 'hilly', 9: 'mountain', 10: 'hilly',
    11: 'mountain', 12: 'hilly', 13: 'itt', 14: 'hilly', 15: 'mountain',
    16: 'mountain', 17: 'hilly', 18: 'mountain', 19: 'hilly', 20: 'mtn_itt', 21: 'flat'
}

class StageCalendar:
    """Manages the 21-stage TDF simulation schedule."""
    
    def __init__(self, start_date: date):
        self.start_date = start_date
        self.stages = self._generate_stage_schedule()
    
    def get_today_stage(self, today: date) -> Dict[str, Any] | None:
        """Get today's stage information."""
        
    def get_upcoming_stages(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming stages for planning."""
        
    def is_rest_day(self, today: date) -> bool:
        """Check if today is a scheduled rest day."""
```

#### 3.2 Integrate with Mission Config
**Update**: `src/lanterne_rouge/mission_config.py`

```python
class TDFMissionConfig(MissionConfig):
    """Extended mission config for TDF simulation."""
    simulation_start_date: date
    stage_calendar: Dict[int, str]  # stage_number -> stage_type
    rest_days: List[int]  # stage numbers that are rest days
```

### Phase 4: Points Calculation System

#### 4.1 Points Calculator
**New file**: `src/lanterne_rouge/points_calculator.py`

```python
from typing import Dict, List, Tuple

POINTS_TABLE = {
    'flat': {'gc': 5, 'breakaway': 8},
    'hilly': {'gc': 7, 'breakaway': 11}, 
    'mountain': {'gc': 10, 'breakaway': 15},
    'itt': {'gc': 4, 'breakaway': 6},
    'mtn_itt': {'gc': 6, 'breakaway': 9}
}

BONUS_CRITERIA = {
    'consecutive_5': {'threshold': 5, 'points': 5},
    'breakaway_10': {'threshold': 10, 'points': 15},
    'all_mountains_breakaway': {'points': 10},
    'final_week_complete': {'points': 10},
    'all_gc_mode': {'points': 25}
}

class PointsCalculator:
    """Calculates points and tracks bonus progress."""
    
    def calculate_stage_points(self, stage_type: str, mode: str) -> int:
        """Calculate points for a completed stage."""
        
    def check_bonus_eligibility(self, completion_data: Dict) -> Dict[str, int]:
        """Check which bonuses have been earned."""
        
    def get_points_summary(self) -> Dict[str, Any]:
        """Get complete points status and projections."""
```

### Phase 5: Enhanced Communication System

#### 5.1 Update CommunicationAgent
**File**: `src/lanterne_rouge/ai_clients.py`

```python
class TDFCommunicationAgent(CommunicationAgent):
    """Enhanced communication agent for TDF simulation."""
    
    def generate_morning_briefing(
        self,
        tdf_decision: TDFDecision,
        stage_info: Dict[str, Any],
        points_status: Dict[str, Any]
    ) -> str:
        """Generate morning briefing with ride mode recommendation."""
        
    def generate_evening_summary(
        self,
        stage_results: Dict[str, Any],
        points_earned: int,
        total_points: int,
        bonus_progress: Dict[str, Any]
    ) -> str:
        """Generate evening summary with points and progress."""
```

#### 5.2 Enhanced Prompts for LLM
**LLM System Prompt Extensions**:

```python
TDF_SYSTEM_PROMPT = """You are an expert cycling coach for the Tour de France Indoor Simulation.
Your athlete is competing in a 21-stage simulation with a points-based scoring system.

RIDE MODES:
- GC Mode (Conservative): Lower risk, base points only, focus on completion
- Breakaway Mode (Aggressive): Higher intensity, bonus points, higher risk

POINTS STRUCTURE:
- Flat: GC=5pts, Breakaway=8pts
- Hilly: GC=7pts, Breakaway=11pts  
- Mountain: GC=10pts, Breakaway=15pts
- ITT: GC=4pts, Breakaway=6pts
- Mountain ITT: GC=6pts, Breakaway=9pts

BONUSES:
- 5 consecutive stages: +5pts
- 10+ Breakaway stages: +15pts
- All mountains in Breakaway: +10pts
- Complete final week: +10pts
- All stages in GC mode: +25pts

Your responses should include:
1. Recommended ride mode with clear rationale
2. Points opportunity explanation  
3. Strategic context for upcoming stages
4. Motivation and encouragement"""
```

### Phase 6: Integration and Workflow Updates

#### 6.1 Update Daily Execution Flow
**File**: `scripts/daily_run.py`

```python
def run_tdf_daily_logic():
    """Execute TDF-enhanced daily logic."""
    # Load mission config
    mission_cfg = bootstrap(Path("missions/tdf_sim_2025.toml"))
    
    # Get current metrics
    readiness, *_ = get_oura_readiness()
    ctl, atl, tsb = get_ctl_atl_tsb()
    
    # Get TDF-specific context
    stage_calendar = StageCalendar(mission_cfg.simulation_start_date)
    today_stage = stage_calendar.get_today_stage(date.today())
    points_status = get_current_points()
    
    # Create enhanced metrics package
    metrics = {
        "readiness_score": readiness,
        "ctl": ctl, "atl": atl, "tsb": tsb,
        "stage_info": today_stage,
        "points_status": points_status
    }
    
    # Initialize TDF Coach
    tdf_coach = TDFTourCoach(mission_cfg)
    
    # Generate morning briefing
    morning_briefing = tdf_coach.generate_morning_briefing(metrics)
    
    return morning_briefing, metrics
```

#### 6.2 Create Evening Points Summary Script
**New file**: `scripts/evening_tdf_summary.py`

```python
def generate_evening_summary():
    """Generate evening points summary after workout completion."""
    # Check if workout was completed today
    # Calculate points earned
    # Update running totals
    # Check bonus achievements
    # Generate summary with progress
```

### Phase 7: User Interface Enhancements

#### 7.1 Enhanced Output Format
**Morning Notification Template**:

```
🏆 TDF Simulation - Stage {stage_number} ({stage_type.title()})

📊 READINESS CHECK:
• Score: {readiness}/100
• TSB: {tsb}
• CTL: {ctl}

🎯 TODAY'S STRATEGY:
• Recommended Mode: {recommended_mode.upper()}
• Rationale: {mode_rationale}
• Expected Points: {expected_points}

🏔️ STAGE DETAILS:
• Type: {stage_type.title()} Stage
• Target Zones: {target_zones}
• Duration: {duration} minutes

📈 POINTS STATUS:
• Current Total: {total_points}
• Consecutive Stages: {consecutive_count}
• Bonus Progress: {bonus_progress}

🎪 STRATEGIC NOTES:
{strategic_context}
```

**Evening Summary Template**:

```
🎉 Stage {stage_number} Complete!

✅ PERFORMANCE:
• Mode Completed: {actual_mode.upper()}
• Stage Points: +{stage_points}
• Bonus Points: +{bonus_points}

📊 UPDATED TOTALS:
• Total Points: {total_points}
• Stages Completed: {stages_completed}/21
• Consecutive Streak: {consecutive_streak}

🏆 BONUS PROGRESS:
• 5 Consecutive: {consecutive_progress}
• 10 Breakaways: {breakaway_progress}  
• Mountain Breakaways: {mountain_progress}

🔮 TOMORROW:
Stage {next_stage_number} ({next_stage_type}) - {preview}
```

### Phase 8: Testing and Validation

#### 8.1 Unit Tests
**New file**: `tests/test_tdf_points.py`

```python
def test_points_calculation():
    """Test points calculation for all stage types and modes."""
    
def test_bonus_tracking():
    """Test bonus achievement tracking."""
    
def test_ride_mode_recommendations():
    """Test ride mode recommendation logic."""
    
def test_stage_scheduling():
    """Test stage calendar functionality."""
```

#### 8.2 Integration Tests
**New file**: `tests/test_tdf_integration.py`

```python
def test_full_daily_workflow():
    """Test complete daily workflow with TDF enhancements."""
    
def test_points_persistence():
    """Test points data persistence across days."""
```

### Phase 9: Configuration and Setup

#### 9.1 Enhanced Mission Config
**Update**: `missions/tdf_sim_2025.toml`

```toml
# Add TDF-specific configuration
[tdf_simulation]
simulation_start_date = 2025-07-05
total_stages = 21
rest_days = [8, 15]  # Stage numbers for rest days
points_target = 150  # Target total points

[stage_types]
flat_stages = [1, 4, 7, 21]
hilly_stages = [2, 3, 5, 8, 10, 12, 14, 17, 19]  
mountain_stages = [6, 9, 11, 15, 16, 18]
itt_stages = [13]
mtn_itt_stages = [20]

[scoring]
track_bonuses = true
aggressive_threshold = 0.6  # % of stages that can be Breakaway mode
```

#### 9.2 Database Migration Script
**New file**: `scripts/migrate_tdf_database.py`

```python
def migrate_database():
    """Migrate existing database to support TDF simulation."""
    # Add new tables
    # Initialize stage schedule
    # Set up default values
```

## Implementation Timeline

### Week 1: Core Infrastructure
- [ ] Database schema extensions
- [ ] Points calculation system
- [ ] Stage calendar implementation

### Week 2: Decision System
- [ ] Enhanced ReasoningAgent with ride mode logic
- [ ] TDF-specific decision structures
- [ ] Bonus tracking system

### Week 3: Communication & Integration
- [ ] Enhanced CommunicationAgent
- [ ] Updated daily workflow
- [ ] Morning/evening summary templates

### Week 4: Testing & Polish
- [ ] Comprehensive testing
- [ ] Documentation updates
- [ ] Performance optimization
- [ ] User experience refinements

## Deployment Strategy

1. **Development Branch**: Implement all changes in `feature/tdf-points-system`
2. **Testing**: Run simulation with test data for 7-day period
3. **Gradual Rollout**: Deploy morning recommendations first, then evening summaries
4. **Monitoring**: Track system performance and user engagement
5. **Iteration**: Refine based on real-world usage data

## Risk Mitigation

1. **Backward Compatibility**: Maintain existing non-TDF functionality
2. **Fallback Systems**: Provide manual overrides for mode selection
3. **Data Validation**: Robust error handling for points calculations
4. **Performance**: Optimize database queries for daily operations
5. **User Experience**: Clear error messages and recovery procedures

This implementation plan provides a comprehensive roadmap for adding the TDF points system while maintaining the existing architecture's strengths and ensuring reliable operation throughout the 21-stage simulation.