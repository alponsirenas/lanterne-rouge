# Release Notes v0.5.1 - Project Organization & Workflow Reliability

*Released: July 8, 2025*

This maintenance release focuses on project organization, GitHub Actions reliability, and documentation updates following the TDF power-based analysis implementation.

## 🗂️ Project Structure Improvements

### Documentation Organization
- **Moved 6 documentation files** from root to `docs/` directory
- **Organized scripts** into `scripts/` (core workflows) and `scripts/utils/` (utilities)
- **Created comprehensive documentation** for utility scripts
- **Fixed file extensions** (e.g., `tdf_points` → `tdf_points.md`)
- **Removed system files** and empty configurations

### Scripts Reorganization  
- **Core Scripts** (`scripts/`): Daily workflows and production scripts
- **Utility Scripts** (`scripts/utils/`): Diagnostic, fix, and maintenance tools
- **Added README.md** in utils directory documenting all tools

## 🤖 GitHub Actions Reliability

### Protected Branch Support
- **Enhanced authentication** using `GH_PAT` tokens across all workflows
- **Added `fetch-depth: 0`** for complete git history access
- **Fixed TDF points accumulation** by ensuring workflows start with latest state
- **Improved error handling** and debugging output

### Workflow Updates
- **Daily workflow**: Better token handling and PR creation
- **TDF evening workflow**: Enhanced points file loading and accumulation
- **TDF morning workflow**: Consistent authentication and permissions
- **All workflows**: Now properly handle protected main branch

## 🏷️ Enhanced Labeler System

### Updated Labeler Action
- **Upgraded to v5** from v4 for improved reliability
- **Modernized configuration** format for better pattern matching
- **Enhanced permissions** and trigger conditions
- **Added comprehensive label categories**: root, CI, documentation, source, tests, scripts, config, tdf

### Label Documentation
- **Created setup guide** (`.github/LABELS.md`) with GitHub CLI commands
- **Documented auto-labeling rules** and file patterns
- **Provided troubleshooting** and testing instructions

## 📖 Documentation Updates

### Context Files
- **Updated TDF GitHub Actions setup** to reflect current workflow structure
- **Revised project structure documentation** to match v0.5.1 state
- **Cleaned up outdated references** to removed workflows

### Technical Documentation
- **Enhanced architecture documentation** reflecting current agent structure
- **Updated about project** with current status and capabilities
- **Comprehensive utility script documentation** in utils README

## 🧹 Code Quality Improvements

### File Cleanup
- **Removed empty `.pylintrc`** file causing confusion
- **Cleaned up `.DS_Store`** system files
- **Fixed markdown file extensions** for proper rendering
- **Organized all documentation** into logical directories

### Structure Benefits
- **Cleaner development experience** with organized file structure
- **Easier navigation** and maintenance
- **Self-documenting** project with comprehensive READMEs
- **Professional organization** following standard practices

## 🔧 Technical Details

### Workflow Configuration
```yaml
# Enhanced checkout with PAT token
- uses: actions/checkout@v4
  with:
    token: ${{ secrets.GH_PAT }}
    fetch-depth: 0

# Improved commit action
- uses: EndBug/add-and-commit@v9
  with:
    github_token: ${{ secrets.GH_PAT }}
    sync-labels: true
```

### Project Structure
```
lanterne-rouge/
├── README.md (only markdown in root)
├── docs/ (16 documentation files)
├── scripts/ (8 core workflow scripts)
├── scripts/utils/ (12 utility scripts + README)
├── src/ (source code)
└── [other core directories]
```

## 📊 Current TDF Status

- **19 total points** (3 stages completed: July 5, 6, 7)
- **All GC mode** with correct power-based classifications
- **Points accumulation working** in GitHub Actions
- **Reliable workflow automation** for stage detection

## 🚀 What's Next

- **Test enhanced labeler** on new pull requests
- **Monitor workflow reliability** during continued TDF simulation
- **Potential v0.6.0** features based on TDF completion insights
- **Documentation refinement** based on user feedback

This release establishes a solid foundation for continued development with improved organization, reliability, and maintainability.
