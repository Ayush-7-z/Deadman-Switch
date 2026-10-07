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
Arm the switch, enter the correct PIN before the timer expires, timer resets and monitoring continues.

### Timeout Flow
Arm the switch, do not check in, warning period begins, if no correct PIN is entered registered sandbox files are deleted.

### Warning Check-in
Let the timer expire, enter the correct PIN during the warning period, cleanup is cancelled and monitoring resumes.

### Sandbox Protection
Every deletion target is resolved and validated before deletion. Only files inside the dedicated `sandbox/` directory can be removed. The check is enforced in `core/sandbox.py:safe_target()`.

## Libraries Used

| Library | Purpose |
|---------|---------|
| `customtkinter` | Modern dark-themed GUI widgets (replaces raw tkinter) |
| `bcrypt` | Salted one-way hashing for PIN storage |
| `sqlite3` | Built-in database for persistence (users, settings, events, files) |
| `threading` | Background timer worker so GUI never freezes |
| `pathlib.Path` | Cross-platform path resolution and validation |
| `shutil.copy2` | Copy custom files into sandbox without touching originals |
| `tkinter.filedialog` | Native file picker for custom file import |
| `tkinter.messagebox` | Confirmation dialogs and error alerts |
| `enum.Enum` | Type-safe state machine constants |
| `datetime` | Consistent timestamp formatting for logs |

## Project Structure

```
deadman_switch/
├── main.py                  # Application entry point
├── core/
│   ├── __init__.py
│   ├── authentication.py    # PIN creation, verification (bcrypt)
│   ├── deadman.py           # Timer state machine, cleanup orchestration
│   └── sandbox.py           # Sandbox file management, safety validation
├── database/
│   ├── __init__.py
│   └── database.py          # SQLite schema, queries, event logging
├── gui/
│   ├── __init__.py
│   └── main_window.py       # CustomTkinter UI, countdown, popups
├── data/
│   └── deadman.db           # SQLite database (auto-created)
├── sandbox/                 # Only directory the app can delete from
└── requirements.txt
```

## How the Code Works

### Entry Point (`main.py`)

Creates the `DeadmanApp` window and starts the Tkinter main loop. Nothing else lives here.

### Database Layer (`database/database.py`)

- Opens (or creates) `data/deadman.db` using `sqlite3` with `check_same_thread=False` so the background timer thread can write logs.
- `row_factory = sqlite3.Row` makes query results accessible by column name.
- `init()` creates four tables with `IF NOT EXISTS` so restarts are safe.
- Default settings row: timer=30s, warning=10s.
- Every significant action calls `db.log(event_type, details)` which inserts into the `events` table.

**Tables:**

| Table | Columns | Purpose |
|-------|---------|---------|
| `users` | id, password_hash, created_at | Single bcrypt hash for the app PIN |
| `settings` | id, timer_seconds, warning_seconds, updated_at | One-row config |
| `events` | id, event_type, timestamp, details | Full activity audit trail |
| `demo_files` | id, filename, sandbox_path, created_at, status | File registry (AVAILABLE / DELETED / FAILED / MISSING) |

### Authentication (`core/authentication.py`)

- `Auth.create(password)` — rejects empty PIN, calls `bcrypt.hashpw(password.encode(), bcrypt.gensalt())`, stores the hash (never the plaintext).
- `Auth.verify(password)` — reads the stored hash, calls `bcrypt.checkpw()` for constant-time comparison.

### Sandbox (`core/sandbox.py`)

- `Sandbox.__init__` resolves the sandbox path to `<project>/sandbox/` and creates it if missing.
- `generate(count)` creates `DEMO_FILE_NNN.txt` files with safe placeholder content.
- `safe_target(row)` — the critical safety function:
  1. Resolves both the sandbox root and the target path (eliminates `..` and symlinks).
  2. Checks `target.relative_to(root)` — rejects anything outside the sandbox.
  3. Verifies the filename matches the DB record and that it is a real file (not a directory).
  4. Returns the path only if all checks pass; otherwise returns `None`.
- `remove_file(target)` calls `path.unlink()` and confirms the file is gone.
- `cleanup(on_progress)` iterates registered files, validates each one, deletes it, updates DB status, and reports progress via callback.
- `refresh_registry()` reconciles DB state with what actually exists on disk.

### Deadman State Machine (`core/deadman.py`)

States: `DISARMED` -> `ARMED` -> `WARNING` -> `CLEANUP` -> `COMPLETED`

- `arm()` — clears the stop event, sets state to ARMED, starts a daemon thread running `_run()`.
- `_run()` — the background worker:
  1. Calls `_countdown(ARMED, timer_seconds)` — ticks every second, reports remaining time via `tick` callback.
  2. If countdown completes (not stopped), logs TIMER_EXPIRED and WARNING_STARTED, then calls `_countdown(WARNING, warning_seconds)`.
  3. If warning countdown also completes, sets state to CLEANUP, calls `sandbox.cleanup(self.progress)`.
  4. If not stopped during cleanup, sets state to COMPLETED.
- `checkin()` — only valid in ARMED or WARNING. Resets `remaining` to full timer. If in WARNING, transitions back to ARMED.
- `disarm()` — sets the `threading.Event` stop flag, transitions to DISARMED.
- `_countdown(state, seconds)` — shared loop for both timer phases. Checks `stop.is_set()` each iteration so disarm is responsive.

The worker thread never touches GUI widgets directly. It uses three callbacks (`tick`, `state_changed`, `progress`) that the GUI schedules via `after(0, ...)`.

### GUI Layer (`gui/main_window.py`)

- `DeadmanApp` extends `ctk.CTk`. Dark mode with blue theme.
- Window size is proportional to screen resolution (capped at 720x520 minimum).
- **Header** — title, current state label, large countdown display.
- **Controls** — PIN entry (masked), CHECK IN, ARM SWITCH, EMERGENCY STOP buttons.
- **Settings** — H:M:S timer fields, warning seconds field, SAVE TIMER button.
- **Workspace** — sandbox file list with checkboxes + activity log textbox.
- `on_tick(remaining)` — called from worker thread; uses `self.after(0, ...)` to update the countdown label on the GUI thread.
- `on_state(state)` — updates status label, shows popup on WARNING or COMPLETED.
- `on_progress(...)` — updates the files label with live cleanup stats.
- `setup_pin()` — first-run flow using `CTkInputDialog` for create + confirm.
- `select_custom()` — uses `filedialog.askopenfilename`, copies the chosen file into `sandbox/copied-file/` with `shutil.copy2`. The original is never touched.
- `delete_selected()` — manual multi-file deletion with confirmation, re-validates each path through `safe_target()`.

## Workflow / Pipeline

```
User launches app
       │
       ▼
Database initialized (tables created if missing)
       │
       ▼
First run? ──Yes──► Prompt to create PIN (bcrypt hash stored)
       │ No
       ▼
Load saved timer settings from DB
       │
       ▼
User arms the switch
       │
       ▼
Background thread starts countdown (ARMED)
       │
       ├── User checks in with correct PIN ──► Timer resets, loop continues
       │
       ├── User hits EMERGENCY STOP ──► Thread halts, state = DISARMED
       │
       ▼ (timer reaches 0)
WARNING state begins (popup shown to user)
       │
       ├── User checks in with correct PIN ──► Back to ARMED
       │
       ▼ (warning reaches 0)
CLEANUP state — sandbox files deleted one by one
       │
       ▼
COMPLETED state — final popup shown
```

## Technology Choices

- **SQLite** — lightweight, zero-config, built into Python's stdlib.
- **bcrypt** — stores a salted hash of the PIN; plaintext is never persisted.
- **Background thread** — file processing runs off the GUI thread so the interface never freezes.
- **Tkinter `after()`** — all GUI updates are scheduled on the main thread to avoid cross-thread widget access.
- **Path resolution + `relative_to()`** — prevents directory traversal attacks even if the DB is tampered with.
- **Daemon thread** — the timer thread dies automatically when the main window closes.

## Limitations

This is an educational demonstration, not a secure mechanism for protecting or destroying real personal data. It intentionally cannot delete arbitrary user files.
