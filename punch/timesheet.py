"""In-memory Timesheet implementation."""


class Timesheet:
    """Store time entries in memory."""

    def __init__(self):
        self.entries = []

    def add_entry(self, timestamp, entry_type):
        """Add a new entry."""
        self.entries.append((entry_type, timestamp))

