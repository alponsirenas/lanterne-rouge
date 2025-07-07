# Power-Based Activity Analysis System

## Overview

The Lanterne Rouge TDF simulation uses a scientifically-based power analysis system to intelligently categorize cycling activities and provide strategic coaching recommendations. This system prioritizes power-based metrics over subjective measures, providing more accurate training load assessment and strategic guidance.

## Core Power Metrics

### 1. Intensity Factor (IF)
- **Formula**: `Normalized Power ÷ FTP`
- **Purpose**: Measures relative effort intensity based on athlete's fitness level
- **Ranges**:
  - `< 0.55`: Recovery (Zone 1)
  - `0.55-0.75`: Aerobic (Zone 2)
  - `0.75-0.85`: Tempo (Zone 3)
  - `0.85-0.95`: Threshold (Zone 4)
  - `0.95-1.05`: VO2max (Zone 5)
  - `> 1.05`: Neuromuscular (Zone 6)

### 2. Training Stress Score (TSS)
- **Formula**: `Duration (hours) × IF² × 100`
- **Purpose**: Quantifies overall training load/stress
- **Interpretation**:
  - `< 150`: Low stress
  - `150-300`: Moderate stress
  - `300-450`: High stress
  - `> 450`: Very high stress

### 3. Normalized Power (NP)
- **Source**: Weighted average power from Strava
- **Purpose**: Accounts for power variability during the ride
- **Usage**: Used in IF calculation instead of average power

## TDF Stage Classification

### Ride Mode Thresholds

#### Breakaway Mode (Aggressive)
- **IF Threshold**: ≥ 0.85 (Zone 4+)
- **TSS Threshold**: ≥ 60
- **Strategy**: High-intensity effort pushing physiological limits
- **Points**: Higher rewards for successful completion

#### GC Mode (Conservative)
- **IF Threshold**: ≥ 0.70 (Zone 3+)
- **TSS Threshold**: ≥ 40
- **Strategy**: Sustainable effort focused on consistent completion
- **Points**: Lower but more reliable rewards

#### Rest Mode (Recovery)
- **IF Threshold**: < 0.70
- **TSS Threshold**: < 40
- **Strategy**: Active recovery or very easy effort
- **Points**: Minimal, but preserves energy for future stages

## LLM Integration

### Activity Analysis Process

1. **Power Metrics Calculation**
   ```python
   # Calculate scientific metrics using athlete's FTP
   power_metrics = calculate_power_metrics(activity_data, ftp)
   ```

2. **LLM Analysis**
   ```python
   # LLM analyzes with power-first approach
   system_prompt = f"""
   ANALYSIS FACTORS (prioritize power-based metrics):
   - Intensity Factor (IF): {intensity_factor:.3f}
   - Training Stress Score (TSS): {tss:.1f}
   - Effort Level: {effort_level}
   """
   ```

3. **Validation & Fallback**
   ```python
   # Validate LLM response and fall back to rules if needed
   if llm_analysis_valid:
       return llm_result
   else:
       return rule_based_analysis(power_metrics)
   ```

### Post-Stage Evaluation

The LLM provides comprehensive post-stage analysis including:
- **Performance Assessment**: Analysis of power metrics and effort sustainability
- **Recovery Recommendations**: Based on TSS and physiological stress
- **Strategic Guidance**: Advice for upcoming stages considering current fitness
- **Motivational Support**: Personalized encouragement and progress tracking

## Configuration

### Mission Config (missions/tdf_sim_2025.toml)
```toml
[athlete]
ftp = 128  # Functional Threshold Power in watts

[tdf_simulation.detection]
# Power-based thresholds
breakaway_intensity_threshold = 0.85  # IF for breakaway
breakaway_tss_threshold = 60          # TSS for breakaway
gc_intensity_threshold = 0.70         # IF for GC mode
gc_tss_threshold = 40                 # TSS for GC mode
fallback_suffer_threshold = 100       # Fallback metric
```

### Environment Variables
```bash
USE_LLM_REASONING=true              # Enable LLM analysis
OPENAI_API_KEY=your_key_here        # OpenAI API access
OPENAI_MODEL=gpt-4-turbo-preview    # Model selection
```

## Technical Implementation

### Key Files
- `scripts/evening_tdf_check.py`: Main analysis workflow
- `src/lanterne_rouge/validation.py`: Power metrics calculation
- `src/lanterne_rouge/ai_clients.py`: LLM integration
- `missions/tdf_sim_2025.toml`: Configuration and thresholds

### Power Metrics Function
```python
def calculate_power_metrics(activity_data: Dict[str, Any], ftp: int) -> Dict[str, Any]:
    """Calculate power-based training metrics using athlete's FTP."""
    normalized_power = activity_data.get('weighted_average_watts', 0)
    duration_hours = activity_data.get('duration_minutes', 0) / 60
    
    if normalized_power > 0 and duration_hours > 0:
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

### Analysis Workflow
```python
def analyze_activity_with_llm(activity, stage_info, mission_cfg):
    """Main analysis function with power-based approach."""
    # 1. Validate activity data
    activity_data = validate_activity_data(activity)
    
    # 2. Calculate power metrics
    ftp = mission_cfg.athlete.ftp
    power_metrics = calculate_power_metrics(activity_data, ftp)
    activity_data.update(power_metrics)
    
    # 3. LLM analysis with power context
    if llm_available:
        return llm_analysis(activity_data, stage_info, mission_cfg)
    else:
        return rule_based_analysis(activity_data, stage_info, mission_cfg)
```

## Benefits

### 1. Scientific Accuracy
- Uses established sports science metrics (IF, TSS, NP)
- Relative to individual athlete fitness (FTP-based)
- Objective measurement vs. subjective suffer score

### 2. Intelligent Analysis
- LLM provides contextual interpretation of power data
- Considers stage type, athlete state, and strategic goals
- Adaptive reasoning based on comprehensive data

### 3. Reliable Fallback
- Rule-based analysis when LLM unavailable
- Power-first approach even in fallback mode
- Graceful degradation with maintained accuracy

### 4. Strategic Coaching
- Post-stage evaluation with recovery recommendations
- Strategic guidance for upcoming stages
- Personalized motivation and progress tracking

## Usage Example

```python
# Example analysis output
{
    'ride_mode': 'breakaway',
    'intensity_factor': 0.892,
    'tss': 242.1,
    'effort_level': 'threshold',
    'rationale': 'Aggressive breakaway effort: IF 0.89 (>0.85), TSS 242 (>60), threshold zone',
    'confidence': 0.9
}
```

This power-based analysis system provides the scientific foundation for intelligent TDF simulation coaching, combining objective metrics with AI-powered insights for optimal training guidance.
