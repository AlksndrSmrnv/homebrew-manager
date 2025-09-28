# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python GUI application for managing Homebrew on macOS. The application provides a graphical interface for common Homebrew operations including updating, diagnosing, cleaning, package management, size analysis, and security checking. The current design uses a simple, clean tkinter interface focused on functionality over visual styling.

## Commands

### Running the Application
```bash
# Preferred method - uses launcher script with dependency checks
./start_homebrew_manager.sh

# Direct execution (requires tkinter to be installed)
python3 homebrew_manager.py

# Install dependencies if needed
brew install python-tk
```

### Development
```bash
# Make launcher script executable (one-time setup)
chmod +x start_homebrew_manager.sh

# Test if tkinter is available
python3 -c "import tkinter"

# Check Homebrew installation
brew --version
```

## Architecture

### Core Components

**HomebrewManager Class** (`homebrew_manager.py`):
- Main application class built on tkinter
- Manages GUI layout, user interactions, and Homebrew command execution
- Uses threading for non-blocking command execution
- Implements real-time output display via queue-based communication

**Key Architecture Patterns**:

1. **Threading Model**: GUI operations run on main thread, Homebrew commands execute in background threads
2. **Queue Communication**: `output_queue` bridges between command execution threads and GUI updates
3. **State Management**: `is_running` flag prevents concurrent operations
4. **Error Analysis**: Built-in error pattern matching with suggested solutions

### GUI Structure
- Main window (800x600) with responsive grid layout
- Button panel with 8 operation buttons arranged in 3 rows
- Scrolled text area for real-time command output
- Progress bar with status indicators during operations
- Smart button state management (disabled during operations)

### Homebrew Operations
The application wraps these core Homebrew commands:
- `brew update` - Update Homebrew itself
- `brew doctor` - System diagnostics
- `brew cleanup --prune=all` + `brew autoremove` - Cleanup operations
- `brew upgrade` - Update all packages
- `brew list --formula` + `brew list --cask` - List installed packages
- Package size analysis using directory traversal
- Security checks for outdated packages and known vulnerabilities

### Command Execution Flow
1. User clicks button → `start_progress()` called
2. Commands queued in `run_command_thread()` or `run_multiple_commands_thread()`
3. Background thread executes via `subprocess.Popen`
4. Real-time output sent to `output_queue`
5. Main thread processes queue via `process_queue()` every 100ms
6. Completion triggers `stop_progress()` and error analysis

### Advanced Features

**Package Size Analysis**:
- Uses `get_directory_size()` for accurate size calculation via `os.walk()`
- Analyzes packages in `/opt/homebrew/Cellar/` and fallback to `brew --prefix`
- Provides size statistics, top 20 largest packages, and cleanup recommendations

**Security Checking**:
- `check_known_vulnerabilities()` - checks against database of known vulnerable versions
- `check_suspicious_packages()` - pattern matching for potentially dangerous packages
- `check_homebrew_permissions()` - validates Homebrew directory ownership
- Comprehensive security report with actionable recommendations

## Requirements

- macOS only (checks `sys.platform == 'darwin'`)
- Python 3.x with tkinter support
- Homebrew installed and accessible via PATH
- `python-tk` package (auto-installed by launcher script)

## Error Handling

The application includes intelligent error analysis that matches command patterns to suggest solutions:
- Network/update issues → suggests cache cleanup
- Permission problems → recommends ownership fixes
- Package upgrade failures → suggests individual package updates

## Security Considerations

- No sudo operations performed
- Only standard Homebrew commands executed
- No system file modifications
- User confirmation required for "Full Maintenance" operation