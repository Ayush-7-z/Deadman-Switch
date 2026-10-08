# 🔐 Deadman Switch

A local desktop security application that monitors a user-defined timer and performs a controlled sandbox cleanup operation if the user does not check in before the timer expires.

The project is built with **Python, CustomTkinter, SQLite, and bcrypt**.

---

## 📌 Table of Contents

- [About the Project](#-about-the-project)
- [Why Deadman Switch?](#-why-deadman-switch)
- [Main Features](#-main-features)
- [How It Works](#-how-it-works)
- [Application Workflow](#-application-workflow)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Technologies and Libraries](#-technologies-and-libraries)
- [Core Components](#-core-components)
- [Deadman State Machine](#-deadman-state-machine)
- [Authentication](#-authentication)
- [Sandbox System](#-sandbox-system)
- [Database](#-database)
- [Timer and Background Worker](#-timer-and-background-worker)
- [Application Pipeline](#-application-pipeline)
- [Security Design](#-security-design)
- [Installation](#-installation)
- [Running the Project](#-running-the-project)
- [Configuration](#-configuration)
- [Example Workflow](#-example-workflow)
- [Current Limitations](#-current-limitations)
- [Future Improvements](#-future-improvements)
- [Learning Objectives](#-learning-objectives)
- [Disclaimer](#-disclaimer)
- [Author](#-author)

---

# 🔎 About the Project

**Deadman Switch** is a local desktop application based on the idea of a software deadman switch.

The application expects the user to periodically confirm that they are active. If the user does not check in before the configured timer expires, the application enters a warning period and can then perform a controlled cleanup operation inside its sandbox.

The project combines:

- User authentication
- Configurable timers
- Background monitoring
- Warning periods
- Check-in functionality
- Disarm functionality
- A controlled filesystem sandbox
- SQLite data storage
- Event logging
- A graphical user interface

The project is designed as an **educational cybersecurity and software-engineering project**.

---

# 🎯 Why Deadman Switch?

A deadman switch is a system that expects a user to periodically confirm that everything is okay.

If the expected confirmation does not happen, the system can perform a predefined action.

The concept is related to:

- Safety systems
- Industrial systems
- Transportation systems
- Security systems
- Emergency systems
- Monitoring systems
- Fail-safe mechanisms

This project implements a simplified **local software version** of that concept.

---

# ✨ Main Features

## 🔐 Authentication

The application uses password/PIN-based authentication.

Passwords are not intentionally stored as plain text. The project uses:

```text
bcrypt
```

to generate password hashes and verify credentials.

---

## ⏱️ Configurable Timer

The user can configure:

- Main timer duration
- Warning duration

The timer is monitored in the background.

---

## 🚨 Warning Period

When the main timer expires, the application enters a warning period.

The user gets an additional opportunity to check in or disarm the switch when the current state allows it.

---

## 🟢 Check-In

The user can authenticate during the allowed period to confirm that they are active.

A successful check-in is intended to return the system to normal monitoring.

---

## 🛑 Disarm

The application provides a disarm operation that can stop the deadman process when the current state permits it.

---

## 📁 Protected Sandbox

The application uses a dedicated sandbox directory.

Files inside the sandbox can be registered and used to demonstrate the cleanup mechanism.

The sandbox is intended to provide a controlled boundary so the cleanup process does not intentionally operate on arbitrary system files.

---

## 🗄️ SQLite Database

SQLite is used for local data storage.

The database stores information such as:

- Users
- Settings
- Registered sandbox/demo files
- Application events

---

## 📋 Event Logging

Important application events are recorded.

Examples include:

```text
LOGIN_SUCCESS
LOGIN_FAILED
SWITCH_ARMED
CHECKIN_SUCCESS
WARNING_STARTED
CLEANUP_STARTED
FILE_DELETED
CLEANUP_COMPLETED
DISARMED
```

---

# ⚙️ How It Works

The basic workflow is:

```text
Start Application
       ↓
Authentication
       ↓
Dashboard
       ↓
Configure Timer
       ↓
Arm Deadman Switch
       ↓
Background Timer Starts
       ↓
Timer Running
       ↓
Did User Check In?
      / \
    YES  NO
     ↓    ↓
  Continue Warning
           ↓
       Check-In?
        /     \
      YES      NO
       ↓        ↓
    Resume    Cleanup
                ↓
            Completed
```

---

# 🔄 Application Workflow

## Step 1 — Application Startup

The application starts through:

```text
main.py
```

The required components are initialized and the graphical interface is launched.

---

## Step 2 — Authentication

The user authenticates before accessing protected functionality.

The entered password/PIN is checked against the stored bcrypt hash.

---

## Step 3 — Dashboard

After successful authentication, the user can access the main interface.

The dashboard provides access to:

- Timer settings
- Deadman switch controls
- Sandbox functionality
- Event information

---

## Step 4 — Configure Timer

The user specifies the main timer and warning duration.

Example:

```text
Main Timer:      60 seconds
Warning Period:  30 seconds
```

---

## Step 5 — Arm the Switch

When the user arms the switch:

```text
DISARMED
   ↓
ARMED
```

Background monitoring starts.

---

## Step 6 — Timer Monitoring

The background worker tracks the remaining time while the GUI remains responsive.

---

## Step 7 — Timer Expiration

If the user does not check in before the main timer expires:

```text
ARMED
   ↓
WARNING
```

The warning period starts.

---

## Step 8 — Check-In

The user can authenticate during the allowed period.

A successful check-in is intended to restore normal monitoring.

---

## Step 9 — Cleanup

If the warning period expires without a valid response:

```text
WARNING
   ↓
CLEANUP
```

The sandbox cleanup operation starts.

---

## Step 10 — Completion

After cleanup:

```text
CLEANUP
   ↓
COMPLETED
```

The corresponding event is recorded in the database.

---

# 🏗️ System Architecture

```text
┌──────────────────────────────┐
│            GUI               │
│         CustomTkinter        │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       Application Logic      │
│        Deadman Engine        │
└───────┬───────────┬──────────┘
        │           │
        ▼           ▼
┌─────────────┐ ┌──────────────┐
│   Sandbox   │ │Authentication│
└──────┬──────┘ └──────┬───────┘
       │               │
       └───────┬───────┘
               ▼
       ┌───────────────┐
       │    SQLite     │
       │    Database   │
       └───────────────┘
```

---

# 📂 Project Structure

```text
Deadman-Switch/
│
├── main.py
├── README.md
├── requirements.txt
│
├── core/
│   ├── authentication.py
│   ├── deadman.py
│   └── sandbox.py
│
├── database/
│   └── database.py
│
├── gui/
│   └── main_window.py
│
└── data/
    └── deadman.db
```

> Runtime/generated files such as the database and Python cache files are better kept out of source control in a production repository.

---

# 🧩 Core Components

## `main.py`

The main entry point of the application.

```text
main.py
   ↓
Application startup
   ↓
GUI
```

---

## `core/authentication.py`

Responsible for authentication.

Main responsibilities:

- Create password hashes
- Verify passwords
- Authenticate users

---

## `core/deadman.py`

The main Deadman Switch engine.

It manages:

- Current state
- Timer
- Warning period
- Check-in
- Arming
- Disarming
- Cleanup transition
- Background worker

---

## `core/sandbox.py`

Responsible for the controlled sandbox.

Its responsibilities include:

- Managing the sandbox
- Registering files
- Copying files
- Validating file paths
- Performing cleanup
- Updating file status

---

## `database/database.py`

Provides the SQLite database layer.

It handles:

- Database initialization
- Users
- Settings
- Sandbox/demo files
- Event logs

---

## `gui/main_window.py`

Contains the graphical user interface.

It handles:

- Login screen
- Main dashboard
- Timer controls
- Sandbox interface
- Status display
- User interaction

---

# 🔄 Deadman State Machine

The application uses several states:

```text
DISARMED
   │
   │ ARM
   ▼
ARMED
   │
   │ Timer expires
   ▼
WARNING
   │
   ├── Check-In ──► ARMED
   │
   ├── Disarm ───► DISARMED
   │
   └── Timeout ──► CLEANUP
                       │
                       ▼
                   COMPLETED
```

## DISARMED

The Deadman Switch is inactive.

No countdown is running.

---

## ARMED

The switch is active and the configured timer is being monitored.

---

## WARNING

The main timer has expired.

The user receives a final warning period.

---

## CLEANUP

The warning period has expired without a valid response.

The sandbox cleanup operation starts.

---

## COMPLETED

The cleanup operation has completed and the event history is updated.

---

# 🔐 Authentication

The project uses **bcrypt** for password hashing.

Instead of storing:

```text
password = "123456"
```

the application stores a bcrypt hash.

Conceptually:

```text
User Password
      ↓
    bcrypt
      ↓
Password Hash
      ↓
   SQLite
```

During login:

```text
Entered Password
      ↓
bcrypt verification
      ↓
Compare with stored hash
      ↓
SUCCESS / FAILURE
```

---

# 📁 Sandbox System

The sandbox is an important safety feature.

Instead of allowing cleanup operations against arbitrary locations, the project uses a controlled directory.

Conceptually:

```text
Application
     │
     ▼
  Sandbox
     │
     ├── file1.txt
     ├── file2.pdf
     └── test.zip
```

The cleanup mechanism is intended to operate only on files controlled by the sandbox system.

---

# 🛡️ Sandbox Path Protection

The project resolves filesystem paths before validating them.

The basic security flow is:

```text
Requested File
      ↓
Resolve Path
      ↓
Check Against Sandbox Root
      ↓
Inside Sandbox?
   /        \
 YES        NO
  ↓          ↓
Allow      Reject
```

This helps defend against simple path traversal and path escape attempts.

---

# 🗄️ Database

The application uses **SQLite** as its local database.

The database stores information related to:

```text
Users
Settings
Sandbox/Demo Files
Events
```

A simplified model is:

```text
┌──────────────┐
│    users     │
├──────────────┤
│ id           │
│ password     │
└──────────────┘

┌──────────────┐
│   settings   │
├──────────────┤
│ timer        │
│ warning      │
└──────────────┘

┌──────────────┐
│ demo_files   │
├──────────────┤
│ id           │
│ filename     │
│ sandbox_path │
│ status       │
└──────────────┘

┌──────────────┐
│    events    │
├──────────────┤
│ id           │
│ event        │
│ timestamp    │
└──────────────┘
```

---

# 📚 Technologies and Libraries

| Technology / Library | Purpose |
|---|---|
| **Python** | Main programming language |
| **CustomTkinter** | Modern desktop GUI |
| **Tkinter** | GUI/event-loop foundation |
| **SQLite** | Local database |
| **sqlite3** | Python interface for SQLite |
| **bcrypt** | Password hashing |
| **threading** | Background timer processing |
| **pathlib** | Filesystem path handling |
| **shutil** | File operations |
| **datetime** | Timestamp generation |

Most filesystem, threading, database, and date/time functionality comes from Python's standard library.

---

# 🧵 Timer and Background Worker

The timer is designed to run outside the main GUI execution path.

Conceptually:

```text
GUI
 │
 │ ARM
 ▼
Deadman Engine
 │
 ▼
Background Worker
 │
 ├── Wait
 ├── Track remaining time
 ├── Check current state
 ├── Detect timeout
 │
 └── Notify GUI
```

The purpose of the worker is to keep timer processing from blocking normal GUI interaction.

---

# 🔄 Complete Application Pipeline

```text
                START
                  │
                  ▼
          Initialize Application
                  │
                  ▼
             Load Database
                  │
                  ▼
             Login Screen
                  │
                  ▼
          Authenticate User
                  │
          ┌───────┴───────┐
          │               │
       Failure         Success
          │               │
          │               ▼
          │            Dashboard
          │               │
          │               ▼
          │         Configure Timer
          │               │
          │               ▼
          │              ARM
          │               │
          │               ▼
          │       Start Monitoring
          │               │
          │               ▼
          │        Timer Running
          │               │
          │               ▼
          │         Timer Ends?
          │           /       \
          │         NO         YES
          │         │           │
          │         │           ▼
          │         │        WARNING
          │         │           │
          │         │       Check-In?
          │         │        /     \
          │         │      YES      NO
          │         │       │        │
          │         │       ▼        ▼
          │         │    Continue  CLEANUP
          │         │               │
          │         │               ▼
          │         │            COMPLETED
          │         │
          └─────────┴────────────────
```

---

# 📝 Event Logging Pipeline

Important actions generate database events.

Example:

```text
User presses ARM
      ↓
Deadman state changes
      ↓
Event is logged
      ↓
Event history is updated
```

Typical events include:

```text
SWITCH_ARMED
WARNING_STARTED
CHECKIN_SUCCESS
CLEANUP_STARTED
FILE_DELETED
CLEANUP_COMPLETED
DISARMED
LOGIN_SUCCESS
LOGIN_FAILED
```

---

# 🔒 Security Design

The project demonstrates several security concepts.

## 1. Password Hashing

bcrypt is used instead of storing plaintext passwords.

## 2. Parameterized SQL

Database operations use parameterized queries to reduce SQL injection risk.

## 3. Sandbox Isolation

Filesystem operations are intended to remain inside the controlled sandbox.

## 4. Path Resolution

Filesystem paths are resolved before validation to help prevent simple path traversal.

## 5. Controlled Cleanup

The cleanup process is designed around registered sandbox files rather than arbitrary system locations.

---

# ⚠️ Security Boundary

This project should **not** be considered a production-grade security or data-destruction system.

It is an educational project demonstrating:

- Authentication
- State machines
- File-system security
- Background processing
- SQLite
- GUI development
- Event logging
- Defensive programming

A production system would require substantially stronger controls, testing, recovery mechanisms, and concurrency guarantees.

---

# 💻 Installation

## 1. Clone the Repository

```bash
git clone https://github.com/Ayush-7-z/Deadman-Switch.git
```

Then:

```bash
cd Deadman-Switch
```

---

## 2. Create a Virtual Environment

On Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Main third-party dependencies:

```text
customtkinter
bcrypt
```

---

# ▶️ Running the Project

Run:

```bash
python main.py
```

The application should launch its graphical interface.

General flow:

```text
Launch
  ↓
Login
  ↓
Dashboard
  ↓
Configure Timer
  ↓
Arm
  ↓
Monitor
```

---

# ⚙️ Configuration

The timer can be configured from the graphical interface.

Example:

```text
Timer Duration: 60 seconds
Warning Duration: 30 seconds
```

The values determine when the application moves from normal monitoring into the warning stage.

---

# 🧪 Example Workflow

Suppose:

```text
Timer = 60 seconds
Warning = 30 seconds
```

The workflow is:

```text
00:60
  ↓
Timer Running
  ↓
00:30
  ↓
00:00
  ↓
WARNING
  ↓
30-second warning
  ↓
Check-In?
```

If the user checks in successfully:

```text
WARNING
   ↓
Check-In
   ↓
Normal Monitoring
```

If the user does not respond:

```text
WARNING
   ↓
Timeout
   ↓
CLEANUP
   ↓
Sandbox Files Processed
   ↓
COMPLETED
```

---

# 🧯 Error Handling

The application attempts to handle runtime failures such as:

- Invalid authentication
- Missing files
- File operation failures
- Invalid configuration
- Database errors
- Sandbox path violations

The goal is to prevent expected runtime problems from unnecessarily crashing the entire application.

---

# 📊 Technology Stack

```text
┌───────────────────────────────┐
│          Desktop GUI          │
│        CustomTkinter          │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│         Python Logic          │
│ Authentication / Deadman      │
│ Timer / Sandbox / Events      │
└───────────────┬───────────────┘
                │
        ┌───────┴────────┐
        ▼                ▼
┌──────────────┐  ┌──────────────┐
│    bcrypt    │  │   pathlib    │
│ Authentication│  │ File Safety  │
└──────────────┘  └──────────────┘
                │
                ▼
        ┌──────────────┐
        │    SQLite    │
        │ Local Storage│
        └──────────────┘
```

---

# 📈 Current Limitations

The current version is an educational prototype.

Important areas for future engineering include:

### State Management

The Deadman state machine needs stronger transition control and synchronization.

### Thread Safety

Shared state and database access require stronger concurrency management.

### Testing

A comprehensive automated test suite should be added.

### Application Lifecycle

The background worker should have explicit startup and shutdown handling.

### Database Management

Runtime database files should normally be excluded from source control.

### Repository Hygiene

Generated files such as:

```text
__pycache__/
*.pyc
*.db
```

should normally be excluded using `.gitignore`.

### CI/CD

Automated build, test, lint, and security checks should be added.

---

# 🚀 Future Improvements

## 🔐 Stronger Security

- PIN attempt limits
- Login cooldown
- Secure configuration
- Better secret management
- Tamper detection

## 🧵 Better Concurrency

- Thread-safe state management
- Controlled worker lifecycle
- Proper synchronization
- Atomic state transitions

## 🧪 Automated Testing

Add tests for:

```text
Authentication
Timer
State transitions
Check-in
Warning
Cleanup
Sandbox security
Database
Error handling
```

## 🗄️ Better Database Architecture

Future versions could introduce:

- Repository pattern
- Database migrations
- Stronger database constraints
- Better transaction management

## 🔄 Recovery

The application could be improved to recover from:

- Unexpected shutdown
- Application crashes
- Worker failure
- Database interruption

## 🔧 CI/CD

A future pipeline could be:

```text
Git Push
   ↓
GitHub Actions
   ↓
Install Dependencies
   ↓
Compile Check
   ↓
Unit Tests
   ↓
Lint
   ↓
Security Scan
   ↓
Build
   ↓
Release
```

---

# 🎓 Learning Objectives

This project demonstrates practical concepts in:

## Python

- Modules
- Classes
- Exception handling
- File handling
- Threads
- SQLite
- GUI programming

## Software Engineering

- Modular architecture
- Separation of responsibilities
- State machines
- Database abstraction
- Error handling
- Application lifecycle

## Cybersecurity

- Password hashing
- Input validation
- Path traversal protection
- Sandboxing
- Security logging
- Defensive programming

## Operating Systems

- Threads
- Filesystems
- File operations
- Background execution

## Databases

- SQLite
- Tables
- CRUD operations
- Transactions
- Event logging

---

# 📌 Project Summary

**Deadman Switch** is a Python-based desktop security project that combines a configurable timer, authentication, sandboxed file management, SQLite logging, and a graphical interface.

The core concept is:

```text
User
 ↓
Authenticate
 ↓
Configure
 ↓
ARM
 ↓
Timer
 ↓
Check-In?
 ├── YES → Continue Monitoring
 │
 └── NO → Warning
             │
             ├── Check-In → Continue
             │
             └── Timeout → Cleanup
                              ↓
                           Completed
```

The project demonstrates how multiple software components can be combined into one security-oriented desktop application.

---

# ⚠️ Disclaimer

This project is intended for **educational, research, and demonstration purposes**.

The cleanup mechanism should only be used with files placed inside the application's controlled sandbox.

Do not configure the application to operate on important system files, operating-system directories, or files that cannot be safely recovered.

---

# 👨‍💻 Author

**Ayush Sharma**

Computer Science Engineering

India

---

# ⭐ Project Goals

The long-term goal is to evolve the project from a desktop prototype into a more reliable security-oriented application by improving:

```text
Correctness
    ↓
Architecture
    ↓
Concurrency
    ↓
Security
    ↓
Testing
    ↓
Reliability
    ↓
Automation
    ↓
Scalability
```

The current version establishes the core concept. Future versions should focus on making the state machine reliable, the filesystem boundary stronger, the database layer thread-safe, and the entire project automatically tested.
