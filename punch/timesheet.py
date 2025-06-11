import datetime
import sqlite3
from . import config, utils


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
        if type not in ("in", "out"):
            raise ValueError("Invalid entry type: {}".format(type))

        cursor = self.conn.cursor()

        # Check previous entry to avoid consecutive identical types
        cursor.execute(
            "SELECT timestamp, type FROM entries WHERE deleted = 0"
            " ORDER BY timestamp DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row is not None and row[1] == type:
            last_timestamp = datetime.datetime.fromtimestamp(row[0])
            raise MismatchedEntryException(
                "Error: last entry was '{}' at {}".format(
                    row[1], last_timestamp.strftime(config.TIMESTAMP_FORMAT)
                )
            )

        cursor.execute(
            "INSERT INTO entries (timestamp, type) VALUES (?, ?)",
            (int(timestamp.timestamp()), type),
        )
        self.conn.commit()

    def delete_last_entry(self):
        # FIXME: implement
        raise NotImplementedError

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

        # FIXME: extract this to a function and test
        sessions = []
        prev_entry_timestamp = None
        prev_entry_type = None
        for row in cursor.fetchall():
            entry_timestamp = datetime.datetime.fromtimestamp(row[1])
            entry_type = row[2]
            if prev_entry_type:
                if entry_type == prev_entry_type:
                    raise MismatchedEntryException(
                        "Error: last entry was '{}' at {}".format(
                            prev_entry_type,
                            prev_entry_timestamp.strftime(config.TIMESTAMP_FORMAT),
                        )
                    )
                if entry_type == "out":
                    sessions.append(Session(prev_entry_timestamp, entry_timestamp))
            else:
                if entry_type == "out":
                    sessions.append(
                        Session(
                            utils.workday_start_for(
                                entry_timestamp, config.WORKDAY_START_TIME
                            ),
                            entry_timestamp,
                        )
                    )
            prev_entry_type = entry_type
            prev_entry_timestamp = entry_timestamp
        if prev_entry_type == "in":
            sessions.append(Session(prev_entry_timestamp, None))
        return sessions


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
