# Deadman File Deletion Switch

Educational 5th-semester CSE desktop project using Python, CustomTkinter, SQLite, bcrypt, timers, background cleanup and event logging.

## Safety

Automatic cleanup is restricted to application files inside `sandbox/`. The program never accepts arbitrary deletion paths, never deletes directories, and never targets Windows/system/user folders.

## Features

- PIN authentication with bcrypt
- Configurable timer and warning period
- Real-time countdown
- Armed, warning, cleanup and completed states
- Emergency stop
- Demo file generation
- Custom file copy into the sandbox
- Multi-file manual deletion
- Real-time sandbox cleanup
- SQLite activity log
- In-app warning and completion popups

## Installation

Python 3.11+ is recommended.

```powershell
python -m pip install -r requirements.txt
python main.py
```

## First run

Create a PIN when prompted. Generate a demo file, set a short timer such as 30 seconds and warning such as 10 seconds, then arm the switch.

## Demonstrations

### Successful check-in
Arm → enter the correct PIN → timer resets.

### Timeout
Arm → do not check in → warning → do not check in → registered sandbox files are processed.

### Warning check-in
Let the timer expire → enter the correct PIN during warning → cleanup is cancelled and monitoring resumes.

### Sandbox protection
Every deletion target is resolved and checked before deletion. Only files inside the dedicated sandbox can be removed.

## Database

`data/deadman.db` contains `users`, `settings`, `events` and `demo_files`.

## Limitations

This is an educational demonstration, not a secure mechanism for protecting or destroying real personal data. It intentionally cannot delete arbitrary user files.

## Viva questions

1. Why SQLite? — It is lightweight and built into Python.
2. Why bcrypt? — It stores a password hash instead of plaintext.
3. Why a background thread? — File processing must not freeze the GUI.
4. What is a deadman switch? — A system that expects periodic check-ins and takes a defined action when check-ins stop.
5. How is deletion restricted? — Targets must resolve inside the dedicated sandbox.
6. Why use `after()` for GUI updates? — Tkinter GUI updates should run on the GUI thread.
