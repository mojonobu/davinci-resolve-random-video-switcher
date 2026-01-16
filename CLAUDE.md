# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a DaVinci Resolve automation tool for splitting video clips at regular intervals. The tool uses the DaVinci Resolve Scripting API (Python) to automate timeline editing operations.

## Running Scripts

DaVinci Resolve must be running before executing any scripts. Scripts can be run via:

```bash
# Ensure PYTHONPATH includes the Resolve modules
# Windows:
set PYTHONPATH=%PYTHONPATH%;%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules\
python src/RandomVideoSwitcher.py
```

Or place scripts in the Resolve Scripts folder to run from the Workspace menu:
- Windows (all users): `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Scripts`
- Windows (user): `%APPDATA%\Roaming\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts`

## Architecture

### Core Components

- `src/RandomVideoSwitcher.py` - Main script that splits clips on video track 1 at 3-second intervals
- `src/python_get_resolve.py` - Utility module to obtain the DaVinci Resolve scripting object (handles cross-platform module discovery)

### DaVinci Resolve API Object Hierarchy

```
Resolve
├── GetProjectManager() → ProjectManager
│   └── GetCurrentProject() → Project
│       ├── GetCurrentTimeline() → Timeline
│       │   └── GetItemListInTrack(trackType, index) → [TimelineItem]
│       └── GetSetting(settingName) → value
└── Fusion()
```

### Key API Patterns

- Get timeline items: `timeline.GetItemListInTrack('video', 1)` returns items on video track 1
- TimelineItem methods: `GetStart()`, `GetDuration()`, `GetEnd()` return frame positions
- Frame rate: `project.GetSetting('timelineFrameRate')` returns fps as string
- Page navigation: `resolve.OpenPage("Edit")` switches to Edit page

## Reference Documentation

The full DaVinci Resolve Scripting API documentation is available at:
`%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\README.txt`

Example scripts are symlinked at `src/ForClaude/Examples(ReadOnly)/` pointing to:
`%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Examples`

## Dependencies

- DaVinci Resolve Studio (required for full scripting API access)
- Python >= 3.6 (64-bit)
