# Deadman File Deletion Switch

Educational 5th-semester CSE desktop project using Python, CustomTkinter, SQLite, bcrypt, timers, background cleanup and event logging.

## What It Does

A deadman switch expects periodic check-ins from the user. If check-ins stop (timer expires), a warning period begins. If no correct PIN is entered during the warning, registered sandbox files are automatically deleted. The entire flow is logged to a local SQLite database.

## Safety

Automatic cleanup is restricted to application files inside `sandbox/`. The program never accepts arbitrary deletion paths, never deletes directories, and never targets Windows/system/user folders.

## Features

- PIN authentication with bcrypt hashing
- Configurable timer and warning period
- Real-time countdown display
- Armed, warning, cleanup and completed states
- Emergency stop button
- Demo file generation for testing
- Custom file copy into the sandbox
- Multi-file manual deletion
- Real-time sandbox cleanup
- SQLite activity log (users, settings, events, demo_files)
- In-app warning and completion popups

## Requirements

- Python 3.11+
- Dependencies: `customtkinter>=5.2.2`, `bcrypt>=4.1.2`

## Installation

```powershell
python -m pip install -r requirements.txt
python main.py
```

## First Run

1. Launch the application — you will be prompted to create a PIN.
2. Generate a demo file from the GUI.
3. Set a short timer (e.g. 30 seconds) and warning period (e.g. 10 seconds).
4. Arm the switch and observe the countdown.

## Usage

### Successful Check-in
Arm the switch → enter the correct PIN before the timer expires → timer resets and monitoring continues.

### Timeout Flow
Arm the switch → do not check in → warning period begins → if no correct PIN is entered, registered sandbox files are deleted.

### Warning Check-in
Let the timer expire → enter the correct PIN during the warning period → cleanup is cancelled and monitoring resumes.

### Sandbox Protection
Every deletion target is resolved and validated before deletion. Only files inside the dedicated `sandbox/` directory can be removed. The check is enforced in `core/deadman.py`.

## Project Structure

```
deadman_switch/
├── main.py                  # Application entry point
├── core/
│   ├── authentication.py    # PIN creation, verification (bcrypt)
│   ├── deadman.py           # Timer logic, cleanup engine, safety checks
│   └── sandbox.py           # Sandbox file management
├── database/
│   └── database.py          # SQLite schema, queries, event logging
├── gui/
│   └── main_window.py       # CustomTkinter UI, countdown, popups
├── data/
│   └── deadman.db           # SQLite database (auto-created)
├── sandbox/                 # Only directory the app can delete from
└── requirements.txt
```

## Database Schema

`data/deadman.db` contains four tables:

| Table | Purpose |
|-------|---------|
| `users` | PIN hashes (bcrypt) |
| `settings` | Timer duration, warning duration |
| `events` | Timestamped log of all actions |
| `demo_files` | Registered demo files eligible for cleanup |

## Technology Choices

- **SQLite** — lightweight, zero-config, built into Python's stdlib.
- **bcrypt** — stores a salted hash of the PIN; plaintext is never persisted.
- **Background thread** — file processing runs off the GUI thread so the interface never freezes.
- **Tkinter `after()`** — all GUI updates are scheduled on the main thread to avoid cross-thread widget access.

## Limitations

This is an educational demonstration, not a secure mechanism for protecting or destroying real personal data. It intentionally cannot delete arbitrary user files.
