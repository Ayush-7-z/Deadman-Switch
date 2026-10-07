import threading
import time
from enum import Enum


class State(Enum):
    # The switch always has exactly one of these states.
    DISARMED = "DISARMED"
    ARMED = "ARMED"
    WARNING = "WARNING"
    CLEANUP = "CLEANUP"
    COMPLETED = "COMPLETED"


class Deadman:
    """Runs the timer and starts sandbox cleanup when it expires."""

    def __init__(self, db, sandbox, tick, state_changed, progress):
        # These callbacks let the timer update the GUI without knowing GUI code.
        self.db = db
        self.sandbox = sandbox
        self.tick = tick
        self.state_changed = state_changed
        self.progress = progress

        # Initial state: the switch is off and no timer is running.
        self.state = State.DISARMED
        self.remaining = 0

        # Event used by the GUI to safely stop the worker thread.
        self.stop = threading.Event()
        self.timer_seconds = 30
        self.warning_seconds = 10

    def configure(self, timer_seconds, warning_seconds):
        # Store the user-selected countdown values.
        self.timer_seconds = timer_seconds
        self.warning_seconds = warning_seconds

    def arm(self):
        # Do not start another worker if the switch is already armed.
        if self.state == State.ARMED:
            return

        self.stop.clear()
        self.remaining = self.timer_seconds
        self.state = State.ARMED
        self.db.log("SWITCH_ARMED")
        self.state_changed(self.state)

        # The countdown runs in the background so the GUI stays responsive.
        threading.Thread(target=self._run, daemon=True).start()

    def checkin(self):
        # A check-in is valid only while the main timer or warning is active.
        if self.state not in (State.ARMED, State.WARNING):
            return False

        # A correct check-in gives the user a completely new timer period.
        self.remaining = self.timer_seconds
        if self.state == State.WARNING:
            # Checking in during WARNING cancels the warning and returns to ARMED.
            self.state = State.ARMED
            self.state_changed(self.state)
        self.db.log("CHECKIN_SUCCESS")
        return True

    def disarm(self):
        # Emergency stop only has an effect while the switch is active.
        if self.state not in (State.ARMED, State.WARNING):
            return

        # Tell the worker loop to stop as soon as possible.
        self.stop.set()
        self.state = State.DISARMED
        self.remaining = 0
        self.db.log("SWITCH_DISARMED")
        self.state_changed(self.state)

    def _countdown(self, state, seconds):
        # This helper is reused for both the main timer and warning timer.
        self.state = state
        self.remaining = seconds
        self.state_changed(state)

        while not self.stop.is_set() and self.state == state:
            # Send the current time to the GUI. The GUI schedules the real widget update.
            self.tick(self.remaining)
            if self.remaining <= 0:
                return True
            time.sleep(1)
            self.remaining -= 1
        return False

    def _run(self):
        # Phase 1: normal countdown.
        if not self._countdown(State.ARMED, self.timer_seconds):
            return

        # Phase 2: timer expired, so give the user one final warning period.
        self.db.log("TIMER_EXPIRED")
        self.db.log("WARNING_STARTED")
        if not self._countdown(State.WARNING, self.warning_seconds):
            return

        # Phase 3: no check-in arrived, so begin deleting registered sandbox files.
        self.state = State.CLEANUP
        self.db.log("CLEANUP_STARTED")
        self.state_changed(self.state)
        self.sandbox.cleanup(self.progress)

        # Only report completion if cleanup was not stopped.
        if not self.stop.is_set():
            self.state = State.COMPLETED
            self.remaining = 0
            self.db.log("CLEANUP_COMPLETED")
            self.state_changed(self.state)
