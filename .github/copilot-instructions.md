# Copilot Instructions for Lanterne Rouge

## Project Overview

Lanterne Rouge is an AI-powered cycling coaching system that integrates data from Oura Ring and Strava to provide personalized daily training recommendations. It includes a Tour de France 2025 indoor simulation and a Fiction Mode that transforms training data into immersive cycling narratives.

## Architecture

### Core Modules (`src/lanterne_rouge/`)
- **ai_clients.py**: OpenAI API integration for LLM-powered reasoning
- **reasoner.py**: Multi-mode reasoning system for training analysis
- **plan_generator.py**: Adaptive training plan generation
- **tour_coach.py**: Daily coaching report generation
- **tdf_tracker.py**: Tour de France simulation tracking with points, classifications, and stage management
- **strava_api.py**: Strava API integration for activity data
- **memory_bus.py**: SQLite database interface for training history
- **mission_config.py**: TOML-based mission configuration loader
- **fiction_mode/**: Dynamic event generation and narrative storytelling system

### Scripts (`scripts/`)
- **daily_run.py**: Main daily execution entry point
- **run_fiction_mode.py**: Fiction Mode narrative generation
- **evening_tdf_check.py**: Evening TDF simulation processing
- **morning_tdf_briefing.py**: Morning TDF briefing generation
- **integrate_tdf_docs.py**: Documentation website integration
- **utils/**: Diagnostic and utility scripts

## Development Guidelines

### Code Style
- Follow PEP 8 with max line length of 100 characters (enforced by flake8)
- Use type hints for function parameters and return values
- Add docstrings to all public functions and classes
- Keep functions focused and modular

### Testing
- Tests are located in `tests/` directory
- Run tests with: `pytest tests/`
- Python path is configured to `src` in `pytest.ini`
- Write tests for new features and bug fixes
- Some pre-existing test failures may exist; don't break working tests

### Linting
- Use flake8 for code linting: `flake8 src/ scripts/`
- Pylint CI runs on push for Python 3.8, 3.9, 3.10
- Configuration in `.flake8`

### Dependencies
- Main dependencies in `requirements.txt`
- Key libraries: openai, pydantic, python-dotenv, streamlit, requests, twilio
- Install with: `pip install -r requirements.txt`

### Database
- SQLite database at `memory/lanterne.db`
- Managed through `memory_bus.py`
- Contains training history, observations, and TDF simulation state

### Environment Variables
Required secrets (configured in `.env` or GitHub Secrets):
- `OURA_TOKEN`: Oura Ring API token
- `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REFRESH_TOKEN`: Strava API credentials
- `OPENAI_API_KEY`: OpenAI API key
- `EMAIL_ADDRESS`, `EMAIL_PASS`, `TO_EMAIL`, `TO_PHONE`: Notification settings
- `GH_PAT`: GitHub Personal Access Token for automation
- `USE_TWILIO`: Toggle for Twilio SMS (optional)

## GitHub Actions Workflows

### Daily Workflows
- **daily.yml**: Main daily coach run at 7AM PT
- **tdf-morning.yml**: Morning TDF briefing
- **tdf-evening.yml**: Evening TDF check and processing
- **tdf-fiction-mode.yml**: Fiction Mode narrative generation

### CI/CD
- **pylint.yml**: Runs on every push for code quality
- **deploy-docs.yml**: Deploys documentation website to GitHub Pages
- **label.yml**: Auto-labeling for PRs

## Documentation

### Structure
- **docs/**: General documentation files
- **docs_src/**: Documentation website source files (MkDocs)
- **mkdocs.yml**: MkDocs configuration
- Website deployed at: https://alponsirenas.github.io/lanterne-rouge/

### Updating Documentation
- Update relevant files in `docs_src/` when making feature changes
- Run `mkdocs serve` locally to preview changes
- Documentation automatically deploys via GitHub Actions

## Common Tasks

### Adding a New Feature
1. Create feature in appropriate module under `src/lanterne_rouge/`
2. Add tests in `tests/test_<module>.py`
3. Update documentation in `docs_src/` if user-facing
4. Run `pytest` and `flake8` before committing
5. Update `VERSION` file if it's a release feature

### Modifying TDF Simulation
- Core logic in `tdf_tracker.py`
- Points calculations, classifications, and stage management
- Stage data in database and mission config files
- Update documentation in `docs_src/tdf-simulation/`

### Working with Fiction Mode
- Core system in `src/lanterne_rouge/fiction_mode/`
- Rider profiles, event generation, and narrative styles
- Test with: `python scripts/utils/test_fiction_mode.py`
- Generate narratives: `python scripts/run_fiction_mode.py --style krabbe`

### Debugging
- Use utility scripts in `scripts/utils/` for diagnostics
- Check database state: `sqlite3 memory/lanterne.db`
- Review output files in `output/` directory
- Check logs from GitHub Actions for automated runs

## Important Patterns

### AI Client Usage
```python
from lanterne_rouge.ai_clients import get_client
client = get_client()
response = client.generate_response(prompt, context)
```

### Database Access
```python
from lanterne_rouge.memory_bus import MemoryBus
bus = MemoryBus("memory/lanterne.db")
bus.store_observation(data)
```

### Mission Configuration
```python
from lanterne_rouge.mission_config import load_config
config = load_config("missions/tdf_sim_2025.toml")
```

## Version Control

- Main branch: `main`
- Feature branches: descriptive names (e.g., `feature/fiction-mode-enhancement`)
- Commit messages: Follow conventional commits (e.g., `feat:`, `fix:`, `docs:`, `chore:`)
- Automated commits from bot use `[skip ci]` to avoid triggering workflows

## Security Considerations

- Never commit secrets or API keys to repository
- Use environment variables or GitHub Secrets for sensitive data
- Validate all external API responses
- Be cautious with user-provided data in database queries

## Current Version: v0.7.0

Latest features:
- Complete Fiction Mode system with dynamic event generation
- Enhanced reasoning system with multiple analysis modes
- Professional project structure with proper module organization
- Automated documentation updates and website deployment
- Full TDF 2025 simulation with 21 stages and multiple classifications

## Helpful Resources

- [Lanterne Rouge Documentation](https://alponsirenas.github.io/lanterne-rouge/)
- [Project Board](https://github.com/users/alponsirenas/projects/2)
- [Release Notes](docs/RELEASE_NOTES_v0.7.0.md)
