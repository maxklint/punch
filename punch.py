import os
import sys
import datetime


def print_usage():
    print("USAGE: punch [in | out]")


def locate_timesheet():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "timesheet.txt")


def load_timesheet(path):
    entries = []
    with open(path, "r") as timesheet:
        lines = timesheet.readlines()
        for line in lines:
            line = line.replace('\r', '').replace('\n', '')
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
                timestamp = datetime.datetime.strptime(line, "%c")
            except:
                continue

            entries.append((type, timestamp))
    return entries


def print_report():
    entries = load_timesheet(locate_timesheet())
    now = datetime.datetime.now()
    entries = [entry for entry in entries if entry[1].date() == now.date()]
    intervals = []
    start = None
    for entry in entries:
        if entry[0] == "in":
            if not start:
                start = entry[1]
        elif entry[0] == "out":
            if start:
                intervals.append(entry[1] - start)
                start = None
    if start:
        intervals.append(now - start)
    seconds = 0
    for interval in intervals:
        seconds += interval.seconds
    hours = seconds / 3600
    minutes = (seconds / 60) % 60
    print("Worked today: {0} hours {1} minutes".format(
        int(hours), int(minutes)))


def new_entry(type):
    with open(locate_timesheet(), "a") as timesheet:
        timestamp = datetime.datetime.now().strftime("%c")
        timesheet.write(timestamp + type + "\n")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print_report()
    elif len(sys.argv) > 2 or sys.argv[1] not in ("in", "out"):
        print_usage()
    else:
        new_entry(sys.argv[1])
