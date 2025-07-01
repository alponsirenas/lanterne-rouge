# Lanterne Rouge Test Suite

This directory contains tests for the Lanterne Rouge training system.

## Main Test Files

- `test_reasoning_modes.py`: Comprehensive test for reasoning modes (LLM-based and rule-based)
- `test_agent_output_llm.py`: Tests LLM-based agent output with various scenarios
- `test_ai_clients.py`: Tests AI client functionality
- `test_bannister_fix.py`: Tests fixes to the Bannister model
- `test_mission_config.py`: Tests mission configuration loading
- `test_plan_generator.py`: Tests workout plan generation
- `test_reasoner.py`: Tests the reasoning agent

## Running Tests

Most tests can be run directly:

```bash
python tests/test_reasoning_modes.py
```

For tests that require special configurations:

```bash
# Set environment variables for testing
export OPENAI_API_KEY=your_api_key
export USE_LLM_REASONING=true
```

## Test Configuration

- `setup.py`: Utility for setting up the Python path for tests
- `.pylintrc-tests`: Lint configuration specific to test files

## Archived Tests

See `archive/README.md` for information about archived tests.
