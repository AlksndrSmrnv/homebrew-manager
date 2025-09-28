# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python GUI application for managing Homebrew on macOS with a modern Apple-style design. The application features glass effects, transparency, and contemporary styling while providing a graphical interface for common Homebrew operations like updating, diagnosing, cleaning, and package management.

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
- Main window (900x700) with responsive grid layout and Apple-style design
- Glass-effect containers with transparency and rounded appearance
- Icon-enhanced button panels for different Homebrew operations
- Scrolled text area with custom styling for real-time command output
- Animated progress bar with emoji status indicators
- Smart button state management during operations
- Modern typography using SF Pro Display fonts

### Homebrew Operations
The application wraps these core Homebrew commands:
- `brew update` - Update Homebrew itself
- `brew doctor` - System diagnostics
- `brew cleanup --prune=all` + `brew autoremove` - Cleanup operations
- `brew upgrade` - Update all packages
- `brew list --formula` + `brew list --cask` - List installed packages

### Command Execution Flow
1. User clicks button → `start_progress()` called
2. Commands queued in `run_command_thread()`
3. Background thread executes via `subprocess.Popen`
4. Real-time output sent to `output_queue`
5. Main thread processes queue updates GUI
6. Completion triggers `stop_progress()` and error analysis

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