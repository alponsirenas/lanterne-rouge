# Archived Test Files

This directory contains test files that have been archived as part of test suite consolidation.

## Reason for Archiving

These test files have been superseded by more comprehensive or improved tests in the main tests directory. They are kept here for reference in case their specific functionality is needed in the future.

## Archived Files

1. `test_agent_output.py`
   - Superseded by `test_agent_output_llm.py` which uses real components instead of mocks
   - More comprehensive and concise testing in the new version

2. `test_default_mode.py` and `test_llm_reasoning.py`
   - Consolidated into `test_reasoning_modes.py`
   - The new test covers both default mode verification and explicit mode testing
   
3. `test_bannister.py`
   - Superseded by `test_bannister_fix.py` which has improved date handling and more functionality
   - The fixed version provides the same test coverage with better implementation

## How to Use

If you need to reference these tests or reincorporate specific functionality, you can find them here. However, the active tests in the parent directory should be used for development and validation.
