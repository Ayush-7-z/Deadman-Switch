import shutil
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.authentication import Auth
from core.deadman import Deadman, State
from core.sandbox import Sandbox
from database.database import Database

# Keep the interface in dark mode with the standard CustomTkinter blue theme.
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class DeadmanApp(ctk.CTk):
    """Main window for the Deadman File Deletion Switch."""
    def __init__(self):
        # Build the main window and connect all project layers together.
        super().__init__()
        self.title("Deadman File Deletion Switch")
        # Size the window from the screen so it works on different monitor sizes.
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        width = min(max(720, int(sw * .92)), sw - 20)
        height = min(max(520, int(sh * .90)), sh - 50)
        self.geometry(f"{width}x{height}")
        self.minsize(720, 520)

        # One shared Database object is passed to the other project classes.
        self.db = Database()
        self.auth = Auth(self.db)
        self.sandbox = Sandbox(self.db)
        # Load the timer values saved during the previous run.
        settings = self.db.settings()
        self.timer_seconds = settings["timer_seconds"]
        self.warning_seconds = settings["warning_seconds"]
        self.file_checks = {}

        # Deadman receives callbacks so it can report timer/state/progress changes to the GUI.
        self.deadman = Deadman(
            self.db, self.sandbox, self.on_tick, self.on_state, self.on_progress
        )
        self.deadman.configure(self.timer_seconds, self.warning_seconds)
        # Build the visible interface only after the core objects are ready.
        self.build()
        self.db.log("APPLICATION_STARTED")
        self.refresh_all()
        # First-time users are asked to create a PIN after the window appears.
        if not self.db.user_exists():
            self.after(300, self.setup_pin)

    # Small helpers keep repeated widget creation easy to read.
    def label(self, parent, text, **kwargs):
        return ctk.CTkLabel(parent, text=text, **kwargs)

    def button(self, parent, text, command, width, **kwargs):
        return ctk.CTkButton(parent, text=text, command=command, width=width, **kwargs)

    def build(self):
        # Build the four main GUI sections from top to bottom.
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.build_header()
        self.build_controls()
        self.build_settings()
        self.build_workspace()

    def build_header(self):
        # Header: project title, current state, and live countdown.
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(16, 8))
        for col in range(3):
            header.grid_columnconfigure(col, weight=1)

        title = ctk.CTkFrame(header, fg_color="transparent")
        title.grid(row=0, column=0, sticky="w")
        self.label(title, "DEADMAN SWITCH", font=("Segoe UI", 30, "bold")).pack(anchor="w")
        self.label(title, "Real-Time File Deletion Demonstration", font=("Segoe UI", 15)).pack(anchor="w", pady=(2, 0))

        status = ctk.CTkFrame(header, fg_color="transparent")
        status.grid(row=0, column=1)
        self.status = self.label(status, "STATUS: DISARMED", font=("Segoe UI", 22, "bold"))
        self.status.pack()
        self.label(status, "Current monitoring state", font=("Segoe UI", 12)).pack(pady=(2, 0))

        timer = ctk.CTkFrame(header, fg_color="transparent")
        timer.grid(row=0, column=2, sticky="e")
        self.countdown = self.label(timer, "00:00", font=("Segoe UI", 48, "bold"))
        self.countdown.pack(anchor="e")

    def build_controls(self):
        # Controls: enter PIN, check in, arm the switch, or stop it.
        box = ctk.CTkFrame(self)
        box.grid(row=1, column=0, sticky="ew", padx=28, pady=6)
        pin_box = ctk.CTkFrame(box, fg_color="transparent")
        pin_box.grid(row=0, column=0, sticky="w", padx=10, pady=7)
        self.pin = ctk.CTkEntry(pin_box, placeholder_text="Enter PIN", show="•", width=250)
        self.pin.pack()
        self.pin_feedback = self.label(pin_box, "", font=("Segoe UI", 11))
        self.pin_feedback.pack(anchor="w", pady=(3, 0))

        buttons = [("CHECK IN", self.checkin, 145), ("ARM SWITCH", self.arm, 145), ("EMERGENCY STOP", self.deadman.disarm, 165)]
        for col, (text, command, width) in enumerate(buttons, 1):
            self.button(box, text, command, width).grid(row=0, column=col, padx=6 if col < 3 else (6, 10))

    def build_settings(self):
        # Settings: choose the main timer and the final warning duration.
        box = ctk.CTkFrame(self)
        box.grid(row=2, column=0, sticky="ew", padx=28, pady=6)
        self.label(box, "Timer (H:M:S)").grid(row=0, column=0, padx=(10, 5), pady=10)

        self.h, self.m, self.sec = [ctk.CTkEntry(box, width=70) for _ in range(3)]
        for col, entry in enumerate((self.h, self.m, self.sec), 1):
            entry.grid(row=0, column=col, padx=3 if col == 2 else 0)
        self.h.insert(0, "0")
        self.m.insert(0, str(self.timer_seconds // 60))
        self.sec.insert(0, str(self.timer_seconds % 60))

        self.label(box, "Warning seconds").grid(row=0, column=4, padx=(20, 5))
        self.warn = ctk.CTkEntry(box, width=80)
        self.warn.insert(0, str(self.warning_seconds))
        self.warn.grid(row=0, column=5)
        self.button(box, "SAVE TIMER", self.save_timer, 125).grid(row=0, column=6, padx=15)

    def build_workspace(self):
        # Workspace contains the sandbox file list and the activity log.
        workspace = ctk.CTkFrame(self)
        workspace.grid(row=3, column=0, sticky="nsew", padx=28, pady=(6, 18))
        workspace.grid_columnconfigure(0, weight=1)
        workspace.grid_rowconfigure(1, weight=1)
        self.build_sandbox(workspace)
        self.build_history(workspace)

    def build_sandbox(self, parent):
        # Sandbox section: create, import, refresh, and manually delete files.
        box = ctk.CTkFrame(parent)
        box.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        box.grid_columnconfigure(0, weight=1)
        self.label(box, "DEMO SANDBOX", font=("Segoe UI", 18, "bold")).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 2))

        buttons = ctk.CTkFrame(box, fg_color="transparent")
        buttons.grid(row=0, column=1, sticky="e", padx=10, pady=(7, 3))
        actions = [
            ("GENERATE 1 DEMO FILE", self.generate, 175),
            ("SELECT CUSTOM FILE", self.select_custom, 155),
            ("REFRESH LIST", self.refresh_files, 125),
            ("DELETE SELECTED", self.delete_selected, 145),
        ]
        for text, command, width in actions:
            self.button(buttons, text, command, width).pack(side="left", padx=3)

        self.files_label = self.label(box, "Files available: 0", anchor="w")
        self.files_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 5))
        self.file_list = ctk.CTkScrollableFrame(box, height=115)
        self.file_list.grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=(5, 10))

    def build_history(self, parent):
        # Activity log shows the latest actions recorded by SQLite.
        box = ctk.CTkFrame(parent)
        box.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(1, weight=1)
        self.label(box, "ACTIVITY LOG", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, sticky="w", padx=14, pady=(8, 3))

        buttons = ctk.CTkFrame(box, fg_color="transparent")
        buttons.grid(row=0, column=1, sticky="e", padx=10, pady=(5, 3))
        self.button(buttons, "REFRESH LOG", self.refresh_history, 115, height=28).pack(side="left", padx=3)
        self.button(buttons, "DELETE LOG", self.delete_log, 105, height=28).pack(side="left", padx=3)
        self.logbox = ctk.CTkTextbox(box, height=120)
        self.logbox.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=14, pady=(0, 12))

    def refresh_all(self):
        # Reload both the sandbox file list and the activity log.
        self.refresh_files()
        self.refresh_history()

    def show_event_popup(self, title, message):
        # Use one reusable popup for both the warning and final completion message.
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("460x240")
        popup.resizable(False, False)
        popup.transient(self)
        popup.attributes("-topmost", True)
        popup.grab_set()
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 460) // 2
        y = self.winfo_y() + (self.winfo_height() - 240) // 2
        popup.geometry(f"460x240+{max(0, x)}+{max(0, y)}")

        frame = ctk.CTkFrame(popup)
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        self.label(frame, title, font=("Segoe UI", 22, "bold")).pack(pady=(22, 8))
        self.label(frame, message, font=("Segoe UI", 14), wraplength=380, justify="center").pack(pady=5)
        self.button(frame, "OK", popup.destroy, 110).pack(pady=(14, 18))
        popup.protocol("WM_DELETE_WINDOW", popup.destroy)
        popup.focus_force()

    def setup_pin(self):
        # First-run PIN setup: create the PIN, confirm it, then store its bcrypt hash.
        pin = ctk.CTkInputDialog(text="Create a PIN/password:", title="First-Time Setup").get_input()
        if not pin:
            messagebox.showwarning("Setup", "A PIN is required to use the switch.")
            return
        confirm = ctk.CTkInputDialog(text="Confirm your PIN/password:", title="First-Time Setup").get_input()
        if pin != confirm:
            messagebox.showerror("Setup", "PINs do not match.")
            return
        self.auth.create(pin)

    def save_timer(self):
        # Read the four timer fields, validate them, and save the new configuration.
        try:
            h, m, s, warning = map(int, (self.h.get(), self.m.get(), self.sec.get(), self.warn.get()))
            total = h * 3600 + m * 60 + s
            if total <= 0 or warning <= 0:
                raise ValueError
            self.timer_seconds = total
            self.warning_seconds = warning
            self.db.save_settings(total, warning)
            self.deadman.configure(total, warning)
            self.db.log("TIMER_CONFIGURED", f"timer={total}s warning={warning}s")
            self.countdown.configure(text=self.fmt(total))
        except ValueError:
            messagebox.showerror("Invalid timer", "Timer and warning must be positive whole seconds.")

    @staticmethod
    def fmt(seconds):
        # Convert total seconds into the simple MM:SS display used by the header.
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def arm(self):
        # ARM starts the deadman timer after ensuring a PIN exists.
        if not self.db.user_exists():
            self.setup_pin()
        if self.db.user_exists():
            self.deadman.arm()

    def checkin(self):
        # CHECK IN is the user's heartbeat: a correct PIN resets the timer.
        if self.deadman.state not in (State.ARMED, State.WARNING):
            self.pin_feedback.configure(text="Switch is not armed.", text_color="gray")
            return
        if self.auth.verify(self.pin.get()):
            self.pin_feedback.configure(text="✓ Password correct", text_color="green")
            self.pin.delete(0, "end")
            self.deadman.checkin()
        else:
            self.pin_feedback.configure(text="✗ Password incorrect — timer not reset", text_color="red")
            self.db.log("CHECKIN_FAILED")

    def on_tick(self, remaining):
        # The worker thread calls this callback; after() safely updates the GUI thread.
        self.after(0, lambda: self.countdown.configure(text=self.fmt(max(0, remaining))))

    def on_state(self, state):
        # State changes arrive from the worker, so schedule all widget changes with after().
        def update():
            text = "STATUS: CLEANUP IN PROGRESS" if state == State.CLEANUP else f"STATUS: {state.value}"
            self.status.configure(text=text)
            if state == State.WARNING:
                self.show_event_popup("⚠ DEADMAN WARNING", "The deadman timer has expired.\n\nCheck-in required before demo cleanup starts.")
            elif state == State.COMPLETED:
                self.show_event_popup("DELETION COMPLETED", "Selected sandbox files have been deleted successfully.")
            self.refresh_all()
        self.after(0, update)

    def on_progress(self, index, total, name, ok, success, failed):
        # Update the sandbox area while automatic cleanup is deleting files.
        percent = index / total * 100 if total else 0
        text = f"CLEANUP PROGRESS: {index}/{total} ({percent:.0f}%)\nCurrent: {name}\nDeleted: {success}   Failed: {failed}"
        self.after(0, lambda: self.files_label.configure(text=text))

    def select_custom(self):
        # Custom files are copied into the sandbox; the original file is never deleted.
        source = filedialog.askopenfilename(title="Select a file to copy into Demo Sandbox")
        if not source:
            return
        source = Path(source)
        destination = self.sandbox.root / "copied-file" / source.name
        try:
            destination.parent.mkdir(exist_ok=True)
            shutil.copy2(source, destination)
            self.db.register_file(destination.name, destination)
            self.db.log("CUSTOM_FILE_COPIED", f"{source.name} -> {destination.name}")
            self.refresh_all()
            messagebox.showinfo("Custom File", f"Copied into sandbox as:\n{destination.name}")
        except Exception as error:
            self.db.log("CUSTOM_FILE_COPY_FAILED", str(error))
            messagebox.showerror("Copy Failed", str(error))

    def delete_log(self):
        # Clear only the SQLite activity history after user confirmation.
        if not messagebox.askyesno("Delete Log", "Delete all activity log entries?"):
            return
        self.db.clear_events()
        self.logbox.delete("1.0", "end")

    def generate(self):
        # Generate one safe demonstration file inside the sandbox.
        made = self.sandbox.generate()
        self.db.log("DEMO_FILES_GENERATED", f"{made} file created")
        self.refresh_all()

    def refresh_files(self):
        # Reconcile the database with the real sandbox before showing files.
        self.sandbox.refresh_registry()
        for widget in self.file_list.winfo_children():
            widget.destroy()

        rows = []
        for row in self.db.registered_files():
            if self.sandbox.safe_target(row):
                rows.append(row)
            else:
                self.db.mark_file(row["id"], "MISSING")

        self.files_label.configure(text=f"Files available: {len(rows)}")
        self.file_checks = {}
        for col in range(2):
            self.file_list.grid_columnconfigure(col, weight=1)

        if not rows:
            self.label(self.file_list, "No files currently available in the sandbox.", font=("Segoe UI", 13)).grid(row=0, column=0, columnspan=2, pady=18)
            return

        for index, row in enumerate(rows):
            var = ctk.BooleanVar()
            ctk.CTkCheckBox(self.file_list, text=row["filename"], variable=var, height=30).grid(
                row=index // 2, column=index % 2, sticky="w", padx=8, pady=3
            )
            self.file_checks[row["id"]] = var

    def delete_selected(self):
        # Manually delete only the files selected by the user from the sandbox list.
        selected = [file_id for file_id, var in self.file_checks.items() if var.get()]
        if not selected:
            messagebox.showwarning("Delete Selected", "Select one or more sandbox files first.")
            return
        if not messagebox.askyesno("Delete Selected", f"Delete {len(selected)} selected sandbox file(s)?"):
            return

        deleted = failed = 0
        for file_id in selected:
            row = self.db.available_file(file_id)
            target = self.sandbox.safe_target(row) if row else None
            if not target:
                failed += 1
                if row:
                    self.db.log("FILE_DELETE_FAILED", f"{row['filename']}: sandbox validation failed")
                continue
            try:
                self.sandbox.remove_file(target)
                self.db.mark_file(row["id"], "DELETED")
                self.db.log("FILE_DELETED", row["filename"])
                deleted += 1
            except Exception as error:
                self.db.log("FILE_DELETE_FAILED", f"{row['filename']}: {error}")
                failed += 1

        self.refresh_all()
        messagebox.showinfo("Delete Selected", f"Deleted: {deleted}\nFailed: {failed}")

    def refresh_history(self):
        # Replace the text box contents with the newest database events.
        self.logbox.delete("1.0", "end")
        for row in self.db.events():
            details = row["details"] or ""
            self.logbox.insert("end", f"{row['timestamp']}  {row['event_type']}  {details}\n")


if __name__ == "__main__":
    DeadmanApp().mainloop()