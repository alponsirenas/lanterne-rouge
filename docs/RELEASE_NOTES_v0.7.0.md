# Release Notes v0.7.0 - Fiction Mode & Major Enhancements

*Released: January 15, 2025*

This major release introduces the groundbreaking **Fiction Mode** feature and includes significant project reorganization, bug fixes, and workflow improvements. This represents the largest feature addition since the TDF Points System.

## 🎭 Major New Features

### Fiction Mode - Automated Cycling Narrative Generator
- **Complete Fiction Mode System**: Transform your indoor TDF simulation rides into compelling literary narratives
- **Multi-Style Writing**: Generate stories in the style of cycling literature masters like Tim Krabbé, or choose journalistic/dramatic styles
- **Intelligent Data Integration**: 
  - Automatic Strava ride detection and ingestion
  - Official race data scraping from letour.fr
  - Smart mapping of your effort intervals to real race events
- **Role Assignment**: AI-powered analysis assigns you plausible roles (breakaway, peloton, domestique) based on your effort patterns
- **Technical Authenticity**: Includes power data, heart rate, and tactical cycling details in narratives
- **Delivery System**: Automated story generation and output management

### Enhanced LLM Integration
- **Advanced Analysis Engine**: LLM-powered intelligent analysis of cycling performance and race dynamics
- **Contextual Narrative Generation**: AI generates context-aware stories that blend your data with race reality
- **Multiple AI Client Support**: Flexible AI backend system supporting various LLM providers

## 🏗️ Project Structure Overhaul

### Complete Codebase Reorganization
- **Moved Fiction Mode Core**: `configure_rider_profile.py` relocated to `src/lanterne_rouge/fiction_mode/`
- **Scripts Organization**:
  - **Production Scripts**: Kept in `scripts/` for user-facing functionality
  - **Demo Scripts**: Moved to new `scripts/demo/` directory
  - **Utility Scripts**: Organized in `scripts/utils/` for maintenance tools
- **Documentation Consolidation**: All markdown files moved to `docs/` directory
- **Test Suite Cleanup**: Removed empty test files, organized real tests in `tests/`

### New Fiction Mode Modules
```
src/lanterne_rouge/fiction_mode/
├── __init__.py
├── analysis.py          # Performance analysis
├── configure_rider_profile.py  # Rider profile configuration
├── data_ingestion.py    # Strava and race data ingestion
├── delivery.py          # Story output management
├── editor.py           # Narrative editing and refinement
├── pipeline.py         # Fiction generation pipeline
├── rider_profile.py    # Rider profile management
└── writer.py           # Core narrative generation
```

## 🐛 Critical Bug Fixes

### TDF Points System Reliability
- **Duplicate Activity Prevention**: Fixed race condition preventing duplicate activity counting
- **Timezone Handling**: Added proper timezone support for activity detection across different regions
- **Points Accumulation**: Improved reliability of daily points calculation and persistence

### GitHub Actions Improvements
- **Cron Schedule Fixes**: Corrected timing issues with TDF workflow schedules
- **Workflow Reliability**: Enhanced error handling and state management in automated workflows
- **Authentication**: Improved token handling for protected branch operations

## 📖 Documentation Enhancements

### Fiction Mode Documentation
- **Comprehensive Guide**: Complete documentation for Fiction Mode setup and usage
- **Implementation Summary**: Technical details of the fiction generation system
- **Prompt Compliance**: Guidelines for maintaining narrative quality and factual accuracy

### TDF Simulation Narratives
- **Stage-by-Stage Stories**: Added narrative summaries and tactical stories for TDF Stages 1-9
- **Enhanced Context**: Rich storytelling context for simulation participants
- **Classification System**: Improved documentation of TDF points and classification systems

## 🔧 Technical Improvements

### Code Quality
- **Lint Fixes**: Comprehensive linting improvements across Fiction Mode modules
- **Type Safety**: Enhanced type annotations and error handling
- **Modular Architecture**: Clean separation of concerns in fiction generation pipeline

### Dependencies
- **Updated Requirements**: Added dependencies for web scraping, narrative generation, and enhanced AI integration
- **Compatibility**: Maintained backward compatibility with existing TDF simulation features

## 🚀 New Scripts and Tools

### Fiction Mode Scripts
- `scripts/run_fiction_mode.py` - Main fiction mode execution script
- `scripts/fiction_mode_evening.py` - Evening fiction mode workflow
- `scripts/configure_rider_profile.py` - Wrapper for rider profile configuration

### Enhanced Existing Scripts
- **Morning TDF Briefing**: Enhanced with fiction mode integration
- **Evening TDF Check**: Improved activity detection and processing
- **Tour Coach**: Better integration with new analysis capabilities

## 🎯 Performance & Reliability

### Data Processing
- **Improved Activity Detection**: More reliable Strava activity ingestion
- **Enhanced Error Handling**: Better resilience in data processing pipelines
- **Optimized Performance**: Faster narrative generation and analysis

### Workflow Automation
- **Daily Coach Outputs**: Consistent daily analysis and recommendation generation
- **Morning Briefings**: Reliable stage briefings and points updates
- **Stage Completion**: Automated stage completion detection and processing

## 🔄 Migration Notes

### For Existing Users
- **Script Locations**: Some utility scripts moved to `scripts/utils/` - update any custom automation
- **Configuration**: Fiction Mode requires new rider profile configuration (see documentation)
- **Dependencies**: Run `pip install -r requirements.txt` to install new dependencies

### For Developers
- **Import Paths**: Fiction Mode modules now in `src/lanterne_rouge/fiction_mode/`
- **Test Structure**: Test files reorganized - update test runner configurations
- **Documentation**: All markdown files now in `docs/` directory

## 📊 Statistics

- **20+ commits** since v0.5.1
- **9 new Python modules** for Fiction Mode
- **3 new script categories** (demo, utils, production)
- **Enhanced documentation** with 10+ new/updated files
- **Improved test coverage** with better organization

## 🌟 What's Next

Fiction Mode v0.7.0 lays the foundation for advanced cycling narrative generation. Future releases will include:
- Enhanced writing styles and personalization
- Multi-language support
- Advanced race simulation integration
- Community sharing features

---

**Installation**: `pip install -r requirements.txt`  
**Documentation**: See `docs/fiction_mode.md` for complete Fiction Mode setup guide  
**Issues**: Report bugs and feature requests on GitHub  

This release represents a significant milestone in making Lanterne Rouge the most immersive indoor cycling simulation platform available.
