import bcrypt


class Auth:
    """Create and verify the app PIN using bcrypt."""

    def __init__(self, db):
        # Auth uses the shared database to save and read the PIN hash.
        self.db = db

    def create(self, password):
        # Never allow an empty PIN.
        if not password:
            raise ValueError("PIN cannot be empty.")

        # bcrypt creates a salted one-way hash, so the real PIN is not stored.
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        self.db.set_password_hash(hashed)
        self.db.log("PASSWORD_CREATED")

    def verify(self, password):
        # Read the saved hash and compare it with the PIN entered by the user.
        stored = self.db.get_password_hash()
        return bool(stored and bcrypt.checkpw(password.encode(), stored))
