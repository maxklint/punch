import datetime
from . import config


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
