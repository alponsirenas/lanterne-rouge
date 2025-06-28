# Python Code Linting Guidelines

This document provides guidelines for addressing linting issues in the Lanterne Rouge Python codebase.

## Progress Summary

- Initial pylint score: 6.86/10
- Current pylint score: 9.24/10 (after systematic fixes and .pylintrc adjustments)

## Automated Fixes Applied

The following issues have been automatically addressed with the `fix_lint_issues.py` script:

- Trailing whitespace (C0303)
- Import order using isort (C0411)
- Line length using autopep8 (C0301)
- Unused imports using autoflake (W0611)
- f-strings without interpolation (W1309)
- Missing encoding in file operations (W1514)

To run the automated fixes:

```bash
python scripts/fix_lint_issues.py
```

Required packages: `autopep8`, `isort`, `autoflake` (the script will prompt to install them if missing)

## Manual Fixes Applied

In addition to automated fixes, the following issues were fixed manually:

- Added missing module docstrings to all source files
- Added missing function docstrings to key functions
- Added timeout parameters to network requests
- Fixed import order in many files
- Added encoding="utf-8" to all file open() calls
- Fixed function/variable naming to meet PEP8 standards
- Simplified boolean expressions where applicable

## Configuration Applied

### Import Errors (E0401) and Import Position Issues (C0413)

These issues occur because of the project structure where imports often need to happen after sys.path modifications. We've configured `.pylintrc` to:

1. Add this initialization hook to help pylint find our modules:
   ```
   init-hook='import sys; import os; sys.path.append(os.path.dirname(os.path.abspath("src")))'
   ```

2. Disable import position warnings:
   ```
   disable=C0413,E0401
   ```

Alternatively, for a cleaner approach in the future, consider making this project a proper installable package with pip and setuptools.

### Function Naming in Tests (C0103)

Many test function names are too long and don't conform to the pylint pattern. Options:

1. Rename test functions to use shorter names (though this might reduce readability)
2. Disable this check for test files specifically:
   ```python
   # pylint: disable=C0103  # At the top of the test file
   ```

### Complex Functions (R0912, R0914, R0915)

For complex functions, we've:
1. Increased the thresholds in .pylintrc:
   - max-locals=20 (was 15)
   - max-branches=15 (was 12)
   - max-statements=60 (was 50)

For further improvements, consider:
1. Refactoring these functions into smaller, more focused functions
2. Extracting helper functions for specific tasks
3. Using dataclasses or namedtuples to group related variables

### Broad Exception Handling (W0718)

Some functions catch too broad exceptions (Exception, BaseException). Consider:
1. Catching specific exceptions (like requests.RequestException)
2. If a broad catch is necessary, add a comment explaining why

## Enforcing Linting

The project now has:

1. A pre-commit hook that runs pylint on staged Python files before commit
2. `scripts/check_all_pylint.sh` to check all Python files for linting issues

To check all files:
```bash
./scripts/check_all_pylint.sh
```

## Next Steps

- All files now have scores above 8.0!
- Consider adding additional linting tools like flake8 or black for even more comprehensive checks
- Set up CI/CD integration to enforce linting on pull requests
- For future code, maintain high quality by following these guidelines from the start
