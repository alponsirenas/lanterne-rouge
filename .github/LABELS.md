# Required Labels for Auto-Labeler

This repository uses the GitHub Actions labeler to automatically apply labels to pull requests based on the files changed.

## Required Labels

The following labels need to be created in the GitHub repository for the auto-labeler to work:

### Core Labels
- **`root`** - Changes to root-level files
- **`CI`** - Changes to GitHub Actions workflows and CI/CD
- **`documentation`** - Changes to documentation files
- **`source`** - Changes to source code
- **`tests`** - Changes to test files
- **`scripts`** - Changes to scripts directory
- **`config`** - Changes to configuration files
- **`tdf`** - Changes related to TDF simulation

## Creating Labels

### Via GitHub UI
1. Go to repository Settings → Labels
2. Click "New label" for each required label
3. Add appropriate colors and descriptions

### Via GitHub CLI
```bash
# Create all required labels at once
gh label create "root" --color "f9d71c" --description "Changes to root-level files"
gh label create "CI" --color "1d76db" --description "CI/CD and GitHub Actions changes"
gh label create "documentation" --color "0075ca" --description "Documentation updates"
gh label create "source" --color "d73a4a" --description "Source code changes"
gh label create "tests" --color "0e8a16" --description "Test-related changes"
gh label create "scripts" --color "e4e669" --description "Script changes"
gh label create "config" --color "c2e0c6" --description "Configuration changes"
gh label create "tdf" --color "ff6b00" --description "TDF simulation related"
```

## Auto-Labeling Rules

The labeler automatically applies labels based on file patterns:

- **`documentation`**: `docs/**`, `context/**`, `*.md` files
- **`source`**: `src/**` files  
- **`tests`**: `tests/**` files
- **`scripts`**: `scripts/**` files
- **`CI`**: `.github/**` files
- **`config`**: `config/**`, `missions/**`, `*.toml`, `*.json`, `*.yml` files
- **`tdf`**: Files matching `*tdf*` patterns or `output/tdf_points.json`

Labels are applied automatically when PRs are opened, updated, or reopened.
