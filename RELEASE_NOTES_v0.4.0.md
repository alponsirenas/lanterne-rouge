# Lanterne Rouge v0.4.0 Release Notes

## 🚀 Major Enhancements

### Enhanced Agent-Based Architecture
- **Complete system refactoring** to an intelligent agent-based architecture
- **ReasoningAgent**: Dual-mode reasoning with LLM-based as default, rule-based as fallback
- **WorkoutPlanner**: Structured workout plans with detailed time-in-zones
- **CommunicationAgent**: Empathetic, first-person communication style
- **TourCoach**: Central orchestrator ensuring coherent daily recommendations

### LLM Integration
- **GPT-4-turbo-preview** as default reasoning engine
- **First-person, conversational communication** using 'you' and 'your'
- **Contextual analysis** considering training phase, TSB, goals, and readiness
- **Graceful fallback** to rule-based reasoning when LLM is unavailable

### Enhanced Output Quality
- **Training phase context** with goal countdowns
- **Detailed 150+ word explanations** compared to 7-word rule-based responses
- **Time-in-zone workout prescriptions** with intensity recommendations
- **Load estimation** for training stress quantification
- **Structured, consistent format** across all modes

## 🛠️ Bug Fixes

### Bannister Model Enhancements
- **Fixed CTL, ATL, and TSB calculations** to match intervals.icu reference values
- **Improved TSB calculation** to use today's CTL/ATL values
- **Fixed timezone handling** for consistent datetime comparisons
- **Prioritized power-based TSS** calculations for better accuracy
- **Improved FTP handling** with proper athlete-specific values from mission config

### Error Handling
- **Fixed readiness score handling** to work with scalar integer value instead of dict
- **Improved error handling** for missing or malformed data
- **Enhanced robustness** of the daily pipeline

## 🧰 Developer Tools & Documentation

### Linting and Code Quality
- **Added .pylintrc configuration** for project-specific linting rules
- **Added LINTING_GUIDELINES.md** with coding standards
- **Created fix_lint_issues.py** utility script

### Diagnostic Tools
- **Added compare_data_sources.py** to validate data consistency
- **Added compare_db_vs_calc.py** for database verification
- **Added diagnose_bannister.py** for testing Bannister model calculations
- **Added test_power_tss.py** and **test_tsb_parameters.py** for validation

### Documentation
- **Updated architecture.md** with agent-based system design
- **Added bannister_model.md** with detailed implementation notes
- **Updated ai_integration.md** with LLM integration approach

### Testing
- **Consolidated and improved test suite**:
  - tests/test_reasoning_modes.py: New comprehensive test for reasoning modes
  - tests/test_agent_output_llm.py: Tests LLM-based agent output with various scenarios
  - **Updated core module tests** to match refactored code
  - **Added test documentation** in tests/README.md
  - **Archived legacy tests** in tests/archive/ with documentation

## ⚙️ Configuration Options

- **LLM reasoning enabled by default** via `USE_LLM_REASONING=true` environment variable
- **Configurable models** via `OPENAI_MODEL` environment variable
- **Backwards compatible** with existing workflows
- **Dynamic FTP values** used consistently for power-based TSS calculations

## 📊 Data Management

- **Updated test data files** with cleaned formats
- **Added export_strava_for_testing.py** utility
- **Added manage_memory_db.py** for database maintenance

## 📋 Upgrade Guide

1. Set `USE_LLM_REASONING=true` to enable the LLM-based reasoning (default)
2. Set `USE_LLM_REASONING=false` to revert to rule-based reasoning if needed
3. Ensure `OPENAI_API_KEY` is properly configured for LLM functionality
4. Set `OPENAI_MODEL` to specify an alternative model (default: gpt-4-turbo-preview)
5. Update any code that assumes readiness_score is a dictionary structure

## 🔄 Breaking Changes

- **Readiness score structure**: Now returns a scalar integer instead of a dictionary
  - Code that accesses `readiness.get('score')` should now use the direct value
  - Detailed readiness data is now stored in readiness_score_log.csv

## 👥 Contributors

- Ana Luisa Ponsirenas
- lanterne-rouge-bot

## 📅 Released: July 1, 2025
