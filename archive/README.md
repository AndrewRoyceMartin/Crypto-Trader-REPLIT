# Archive Directory

This directory contains files that were part of the development process but are no longer actively used in the current unified dashboard implementation.

## Directory Structure

### unused_python_files/
Contains Python scripts that are no longer needed:
- Old bot implementations (bot_old.py)
- Deprecated web interface (web_interface.py, main.py)
- Debug and testing utilities
- One-time setup scripts

### unused_templates/
Contains HTML templates replaced by unified_dashboard.html:
- Separate page templates (index.html, portfolio.html, etc.)
- Test templates
- Multi-screen layouts

### unused_css/
Contains CSS files replaced by style_clean.css:
- Old styling systems (style.css, style_modern.css)
- Backup JavaScript files
- Theme toggle implementations

### unused_test_files/
Contains testing files, reports, and temporary data:
- Test scripts and configurations
- Sample data files
- Performance reports

### old_reports/
Contains documentation and analysis reports from development:
- Implementation reports
- Performance analysis
- Architecture guides
- Troubleshooting documentation

## Current Active Files

The current system uses:
- **app.py** - Main Flask application
- **templates/unified_dashboard.html** - Single-page dashboard
- **static/style_clean.css** - Clean minimal styling
- **static/app_clean.js** - Dashboard functionality
- **src/** - All source code modules
- **replit.md** - Project documentation

All archived files are preserved for reference but not loaded by the current system.