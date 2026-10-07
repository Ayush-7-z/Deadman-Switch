import sqlite3
from datetime import datetime
from pathlib import Path

# Store the SQLite database in the project's data folder.
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "deadman.db"


class Database:
    """Small SQLite wrapper used by the application."""

    def __init__(self):
        # Create the data folder before opening the database.
        DB_PATH.parent.mkdir(exist_ok=True)
        # check_same_thread=False is needed because the timer worker also writes logs.
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init()

    @staticmethod
    def now():
        # Keep all activity timestamps in one consistent format.
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def init(self):
        # Create every table the project needs. IF NOT EXISTS keeps startup safe on later runs.
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,password_hash BLOB NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1),timer_seconds INTEGER NOT NULL,warning_seconds INTEGER NOT NULL,updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,event_type TEXT NOT NULL,timestamp TEXT NOT NULL,details TEXT);
        CREATE TABLE IF NOT EXISTS demo_files(id INTEGER PRIMARY KEY,filename TEXT NOT NULL UNIQUE,sandbox_path TEXT NOT NULL,created_at TEXT NOT NULL,status TEXT NOT NULL);
        """)

        # The settings table always has one default row on a brand-new installation.
        if not self.conn.execute("SELECT 1 FROM settings WHERE id=1").fetchone():
            self.conn.execute("INSERT INTO settings VALUES(1,30,10,?)", (self.now(),))
        self.conn.commit()

    def log(self, event_type, details=""):
        # Record important actions so the user can review the activity history.
        self.conn.execute(
            "INSERT INTO events(event_type,timestamp,details) VALUES(?,?,?)",
            (event_type, self.now(), details)
        )
        self.conn.commit()

    def user_exists(self):
        # There is only one application PIN, so one row is enough.
        return bool(self.conn.execute("SELECT 1 FROM users LIMIT 1").fetchone())

    def set_password_hash(self, value):
        # Replace the existing PIN hash instead of keeping multiple passwords.
        self.conn.execute("DELETE FROM users")
        self.conn.execute(
            "INSERT INTO users(password_hash,created_at) VALUES(?,?)",
            (value, self.now())
        )
        self.conn.commit()

    def get_password_hash(self):
        # Return the saved hash, not the original PIN.
        row = self.conn.execute("SELECT password_hash FROM users LIMIT 1").fetchone()
        return row["password_hash"] if row else None

    def settings(self):
        # Load the single saved timer configuration.
        return self.conn.execute("SELECT * FROM settings WHERE id=1").fetchone()

    def save_settings(self, timer_seconds, warning_seconds):
        # Update the saved timer so the values survive application restarts.
        self.conn.execute(
            "UPDATE settings SET timer_seconds=?,warning_seconds=?,updated_at=? WHERE id=1",
            (timer_seconds, warning_seconds, self.now())
        )
        self.conn.commit()

    def register_file(self, filename, path):
        # Reuse an old database row if the same file name is generated again.
        row = self.conn.execute("SELECT id FROM demo_files WHERE filename=?", (filename,)).fetchone()
        if row:
            self.conn.execute(
                "UPDATE demo_files SET sandbox_path=?,status='AVAILABLE' WHERE id=?",
                (str(path), row["id"])
            )
        else:
            self.conn.execute(
                "INSERT INTO demo_files(filename,sandbox_path,created_at,status) VALUES(?,?,?,?)",
                (filename, str(path), self.now(), "AVAILABLE")
            )
        self.conn.commit()

    def registered_files(self):
        # Only AVAILABLE files are candidates for cleanup or manual deletion.
        return self.conn.execute(
            "SELECT * FROM demo_files WHERE status='AVAILABLE' ORDER BY id"
        ).fetchall()

    def available_file(self, file_id):
        # Fetch one file only when it is still marked AVAILABLE.
        return self.conn.execute(
            "SELECT * FROM demo_files WHERE id=? AND status='AVAILABLE'", (file_id,)
        ).fetchone()

    def mark_file(self, file_id, status):
        # Update the registry after a file is deleted or fails validation.
        self.conn.execute("UPDATE demo_files SET status=? WHERE id=?", (status, file_id))
        self.conn.commit()

    def mark_available(self, file_id):
        # Small convenience method used when a known file is found again on disk.
        self.mark_file(file_id, "AVAILABLE")

    def clear_events(self):
        # Remove only the activity history; files and settings remain untouched.
        self.conn.execute("DELETE FROM events")
        self.conn.commit()

    def events(self):
        # Show the newest 200 events first so the GUI stays compact.
        return self.conn.execute(
            "SELECT timestamp,event_type,details FROM events ORDER BY id DESC LIMIT 200"
        ).fetchall()
