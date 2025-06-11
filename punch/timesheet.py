import datetime
import sqlite3
from . import config


class Session:
    def __init__(self, start: datetime.datetime, end: datetime.datetime | None):
        self.start = start
        self.end = end

    def get_start(self) -> datetime.datetime:
        return self.start

    def get_end(self) -> datetime.datetime | None:
        return self.end


class MismatchedEntryException(Exception):
    def __init__(self, message):
        super().__init__(message)


class Timesheet:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        cursor = self.conn.cursor()
        cursor.execute(
            """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY,
    timestamp INTEGER NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('in', 'out')),
    deleted INTEGER NOT NULL DEFAULT 0 CHECK (deleted IN (0, 1))
)
"""
        )
        self.conn.commit()

    def add_entry(self, timestamp: datetime.datetime, type: str):
        # FIXME: check type is in ('in', 'out')
        # FIXME: reject consequtive entries of the same type
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO entries (timestamp, type) VALUES (?, ?)",
            (int(timestamp.timestamp()), type),
        )
        self.conn.commit()

    def get_sessions_in_range(
        self, timestamp: datetime.datetime, delta: datetime.timedelta
    ) -> list[Session]:
        cursor = self.conn.cursor()

        cursor.execute(
            """
        SELECT * FROM entries
        WHERE timestamp BETWEEN ? AND ?
        AND deleted = 0
        ORDER BY timestamp ASC
        """,
            (int(timestamp.timestamp()), int((timestamp + delta).timestamp())),
        )

        # FIXME: convert to sessions
        results = cursor.fetchall()
        for row in results:
            print(row)
        return []


def load_timesheet(path):
    entries = []
    with open(path, "r") as timesheet:
        lines = timesheet.readlines()
        for line in lines:
            line = line.replace("\r", "").replace("\n", "")
            if line.startswith("#"):
                continue
            elif line.endswith(" in"):
                type = "in"
                line = line[:-3]
            elif line.endswith(" out"):
                type = "out"
                line = line[:-4]
            else:
                continue

            try:
                timestamp = datetime.datetime.strptime(line, config.TIMESTAMP_FORMAT)
            except Exception:
                continue

            entries.append((type, timestamp))
    return entries
