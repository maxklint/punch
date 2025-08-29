import datetime
from dataclasses import dataclass
from . import config


@dataclass(frozen=True)
class Entry:
    type: str
    timestamp: datetime.datetime


def load_timesheet(path) -> list[Entry]:
    entries = []
    with open(path, "r") as timesheet:
        lines = timesheet.readlines()
        prev_ts = None
        prev_type = None
        for idx, raw in enumerate(lines, start=1):
            line = raw.replace("\r", "").replace("\n", "")

            # Ignore comments and blank lines entirely
            if not line or line.startswith("#"):
                continue

            if line.endswith(" in"):
                type = "in"
                timestr = line[:-3]
            elif line.endswith(" out"):
                type = "out"
                timestr = line[:-4]
            else:
                raise ValueError(
                    f"Invalid entry format at line {idx}: '{line}' (expected '<timestamp> in|out')"
                )

            try:
                timestamp = datetime.datetime.strptime(timestr, config.TIMESTAMP_FORMAT)
            except Exception:
                raise ValueError(
                    f"Invalid timestamp at line {idx}: '{timestr}' does not match format '{config.TIMESTAMP_FORMAT}'"
                )

            if prev_ts is not None and timestamp < prev_ts:
                raise ValueError(
                    f"Out-of-order entry at line {idx}: {timestamp.isoformat()} is before {prev_ts.isoformat()}"
                )

            if prev_type is not None and type == prev_type:
                raise ValueError(
                    f"Invalid sequence at line {idx}: two consecutive '{type}' entries"
                )

            entries.append(Entry(type=type, timestamp=timestamp))
            prev_ts = timestamp
            prev_type = type
    return entries
