# Fiction Mode - Automated Cycling Narrative Generator

Fiction Mode is an advanced feature of Lanterne Rouge that automatically generates immersive, literary cycling narratives by blending your real Strava ride data with official Tour de France race events.

## Overview

Fiction Mode transforms your indoor TDF simulation rides into compelling stories written in the style of cycling literature masters like Tim Krabbé. It analyzes your power data, heart rate, and effort patterns, then maps them to the actual race events to create a personalized narrative of your "participation" in the Tour de France.

## Features

### Data Integration
- **Strava Integration**: Automatically detects and ingests your TDF simulation rides
- **Race Data Scraping**: Fetches official stage reports, results, and event timelines from letour.fr
- **Smart Mapping**: Aligns your effort intervals with real race events (breakaways, attacks, sprints)

### Narrative Generation
- **Multiple Styles**: Choose from Tim Krabbé, journalistic, or dramatic styles
- **Intelligent Role Assignment**: Assigns you a plausible role (breakaway, peloton, domestique) based on your effort pattern
- **Factual Accuracy**: References real riders, results, and stage events
- **Technical Authenticity**: Includes power, heart rate, and tactical cycling details

### Quality Control
- **Editorial Review**: Automated editing for style consistency and factual accuracy
- **User Feedback**: Incorporate your feedback to refine narratives
- **Quality Scoring**: Style consistency, factual accuracy, and readability scores

### Delivery Options
- **Multiple Formats**: Markdown, HTML, email, JSON
- **Archive System**: Builds a personal season archive of all your stage narratives
- **Metadata**: Rich metadata including performance analysis and stage context

## Usage

### Automatic Detection
Fiction Mode automatically detects TDF simulation rides based on:
- Activity titles containing "Stage X", "TDF Stage X", etc.
- Hashtags like "#TDF2025 Stage 3"
- Activity descriptions mentioning Tour de France stages
- Minimum duration requirements (30+ minutes)

### Running Fiction Mode

#### Command Line
```bash
# Generate narrative for today's ride
python scripts/run_fiction_mode.py

# Preview analysis without generating narrative
python scripts/run_fiction_mode.py --preview

# Process specific activity
python scripts/run_fiction_mode.py --activity-id 12345 --stage 3

# Choose narrative style
python scripts/run_fiction_mode.py --style krabbe

# Different output formats
python scripts/run_fiction_mode.py --format html
```

#### Integration with Evening Workflow
```bash
# Run as part of evening TDF check
python scripts/fiction_mode_evening.py
```

### Narrative Styles

#### Tim Krabbé (`krabbe`)
*Default style inspired by "The Rider"*
- Third person, present tense
- Spare, intelligent prose
- Focus on calculation and internal state
- Attention to technical cycling details
- Subtle, wry observations

#### Journalistic (`journalistic`)
- Clear, factual race reporting
- Past tense, analytical tone
- Tactical explanations
- Professional cycling terminology

#### Dramatic (`dramatic`)
- Emotional, vivid storytelling
- Emphasizes struggle and triumph
- Rich descriptive language
- Epic sports writing style

## Architecture

Fiction Mode consists of five specialized agents:

### 1. Data Ingestion Agents
- **RideDataIngestionAgent**: Fetches Strava ride data, detects TDF activities, extracts effort intervals
- **RaceDataIngestionAgent**: Scrapes stage reports from letour.fr, parses events and results

### 2. Analysis & Mapping Agent
- Analyzes ride intensity and effort distribution
- Maps user efforts to race events (breakaways, attacks, crashes)
- Assigns plausible narrative role based on effort pattern
- Creates timeline for narrative generation

### 3. Writer Agent
- Generates narratives using LLM with style-specific prompts
- Blends user data with real race events
- Maintains factual accuracy while creating engaging stories
- Supports multiple literary styles

### 4. Editor Agent
- Reviews narratives for style consistency
- Checks factual accuracy against stage data
- Improves readability and flow
- Incorporates user feedback for revisions

### 5. Delivery Agent
- Formats narratives in multiple output formats
- Manages archive and metadata
- Handles distribution (email, file storage)
- Creates season compilations

## Configuration

Fiction Mode can be configured through `FictionModeConfig`:

```python
config = FictionModeConfig(
    narrative_style='krabbe',          # krabbe, journalistic, dramatic
    delivery_format='markdown',        # markdown, html, email, json
    include_metadata=True,             # Include performance data
    save_to_archive=True,             # Save to archive
    auto_detect_stage=True,           # Auto-detect stage numbers
    require_min_duration=30,          # Minimum ride duration (minutes)
    user_bio="Experienced cyclist"    # Optional user biography
)
```

## Example Output

```markdown
# Stage 3 — Valenciennes > Dunkerque

*July 7, 2025*

"Merlier Seizes His Opportunity"

⸻

The peloton rolls out in a hush, nerves disguised as boredom. Ana Luisa keeps to the right side of the road, eyes forward, cadence steady—already reading the wind, the posture of rivals, the rumor of a day about to turn ugly. The Tour's third stage is a test of patience and luck, flat but never simple.

At kilometer 15, she responds to the early move, pushing 280 watts as the breakaway forms ahead. The calculation is simple: stay alert, don't waste energy, survive the chaos that will surely come.

The intensity picks up approaching Isbergues as Philipsen steps on his pedals to defend the green jersey. She sees the contact, the high-speed crash that sends yesterday's stage winner to the ground. The peloton splits around the fallen riders, and she holds her line, holding 250 watts through the confusion.

In Dunkirk, as Tim Merlier edges Jonathan Milan at the line, she crosses safely in the bunch. Another day survived, another calculation complete. Tomorrow brings new mathematics, new survival.

---

**Stage:** Valenciennes > Dunkerque  
**Winner:** Tim Merlier (Soudal Quick-Step)  
**Role:** peloton  
**Words:** 387  
**Generated:** July 7, 2025 at 8:45 PM  
```

## File Structure

```
src/lanterne_rouge/fiction_mode/
├── __init__.py              # Package initialization
├── pipeline.py              # Main orchestration pipeline
├── data_ingestion.py        # Strava and race data ingestion
├── analysis.py              # Ride analysis and event mapping
├── writer.py                # Narrative generation
├── editor.py                # Editorial review and quality control
└── delivery.py              # Output formatting and delivery

scripts/
├── run_fiction_mode.py      # Command-line interface
└── fiction_mode_evening.py  # Evening workflow integration

output/fiction_mode/         # Archive directory
├── stage_01_2025-07-05_*.md # Individual stage narratives
└── tdf_2025_complete_season.md # Season compilation
```

## Integration Points

### With Existing Lanterne Rouge Features
- **Strava API**: Uses existing authentication and data fetching
- **AI Clients**: Leverages existing LLM integration
- **Mission Config**: Respects user settings and preferences
- **Evening Workflow**: Can be triggered after activity completion

### With External Services
- **Strava**: OAuth authentication, activity data, streams API
- **letour.fr**: Stage reports and race data scraping
- **OpenAI**: GPT-4 for narrative generation and editing

## Technical Requirements

### Dependencies
- Existing Lanterne Rouge dependencies
- `markdown>=3.6.0` (optional, for HTML formatting)

### Environment Variables
Uses existing Lanterne Rouge environment variables:
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET` 
- `STRAVA_REFRESH_TOKEN`
- `OPENAI_API_KEY`

### Data Sources
- **Strava API**: Activity data, streams, metadata
- **letour.fr**: Official stage reports (web scraping)
- **Static Data**: Stage routes, historical results (fallback)

## Roadmap

### Phase 1: Core Implementation ✅
- Basic pipeline architecture
- Strava integration and TDF activity detection
- Simple race data ingestion
- Tim Krabbé style narrative generation
- Markdown output format

### Phase 2: Enhanced Features
- Advanced race data scraping (multiple sources)
- Real-time Strava streams API integration
- Additional narrative styles
- HTML and email delivery
- User feedback incorporation

### Phase 3: Advanced Features
- Community mode (multiple users in same narrative)
- Photo integration from Strava
- Social media publishing
- Custom style training
- Multi-language support

### Phase 4: Expansion
- Support for other grand tours (Giro, Vuelta)
- Historical Tour recreation
- Running and triathlon narratives
- Mobile app integration

## Contributing

Fiction Mode follows the same contribution guidelines as the main Lanterne Rouge project. Key areas for contribution:

- **Narrative Styles**: Add new literary voices and writing styles
- **Data Sources**: Improve race data scraping and APIs
- **Quality Control**: Enhance editorial algorithms
- **Output Formats**: Add new delivery options
- **Language Support**: Internationalization and localization

See the main [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.
