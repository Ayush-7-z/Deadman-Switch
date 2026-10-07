from pathlib import Path


class Sandbox:
    """Keeps all generated/copied files inside the project's sandbox folder."""

    def __init__(self, db):
        self.db = db

        # The sandbox path is always inside the project directory.
        self.root = Path(__file__).resolve().parent.parent / "sandbox"
        self.root.mkdir(exist_ok=True)

    def _row(self, filename):
        # Find the database record belonging to a file name.
        return self.db.conn.execute(
            "SELECT * FROM demo_files WHERE filename=?", (filename,)
        ).fetchone()

    def generate(self, count=1):
        # Create simple demo text files without touching the user's real files.
        made = 0
        for number in range(1, 10000):
            if made >= count:
                break

            name = f"DEMO_FILE_{number:03d}.txt"
            path = self.root / name
            row = self._row(name)

            # If the file already exists, reuse its database record.
            if path.exists():
                if row and row["status"] != "AVAILABLE":
                    self.db.mark_available(row["id"])
                continue

            path.write_text(
                "This is a Deadman Switch demonstration file.\n"
                "This file is safe to delete.\n",
                encoding="utf-8"
            )
            self.db.register_file(name, path)
            made += 1
        return made

    def safe_target(self, row):
        # Resolve both paths first so '..' and symbolic links cannot escape the sandbox.
        root = self.root.resolve()
        target = Path(row["sandbox_path"]).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            # The file is outside the allowed sandbox, so never delete it.
            return None

        # Also require the expected file name and a real file (not a directory).
        return target if target.name == row["filename"] and target.is_file() else None

    @staticmethod
    def remove_file(target):
        # Delete a validated file and confirm it is really gone.
        # Shared by automatic cleanup and manual "Delete Selected".
        target.unlink()
        if target.exists():
            raise OSError("File still exists after deletion attempt.")

    def refresh_registry(self):
        # First, make database status agree with files that still exist.
        known = set()
        for row in self.db.conn.execute("SELECT * FROM demo_files ORDER BY id").fetchall():
            target = self.safe_target(row)
            if target:
                known.add(target)
                if row["status"] != "AVAILABLE":
                    self.db.mark_available(row["id"])

        # Next, discover files that exist on disk but are missing from the database.
        for path in self.root.rglob("*"):
            if not path.is_file() or path.name == "deadman.db":
                continue
            path = path.resolve()
            if path in known:
                continue

            row = self.db.conn.execute(
                "SELECT id FROM demo_files WHERE sandbox_path=?", (str(path),)
            ).fetchone()
            if row:
                self.db.mark_available(row["id"])
            else:
                self.db.register_file(path.name, path)

    def cleanup(self, on_progress):
        # Cleanup only uses files registered in the database.
        rows = self.db.registered_files()
        success = failed = 0

        for index, row in enumerate(rows, 1):
            try:
                # Validate the path again immediately before deletion.
                target = self.safe_target(row)
                if not target:
                    raise FileNotFoundError("Sandbox validation failed or file is missing.")

                self.remove_file(target)
                self.db.mark_file(row["id"], "DELETED")
                self.db.log("FILE_DELETED", row["filename"])
                success += 1
                ok = True
            except Exception as error:
                # One failure should not stop the cleanup of the remaining files.
                self.db.mark_file(row["id"], "FAILED")
                self.db.log("FILE_DELETE_FAILED", f"{row['filename']}: {error}")
                failed += 1
                ok = False

            # Tell the GUI how many files succeeded/failed so it can show live progress.
            on_progress(index, len(rows), row["filename"], ok, success, failed)

        return success, failed