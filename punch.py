import os
import sys
import datetime
import math

WORKDAY_START_TIME = datetime.time(6, 0, 0)
WORKDAY_SECONDS = 8 * 60 * 60


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


def filter_todays_entries(entries):
    now = datetime.datetime.now()
    start = datetime.datetime(now.year, now.month, now.day,
                              WORKDAY_START_TIME.hour, WORKDAY_START_TIME.minute)
    if now.time() < WORKDAY_START_TIME:
        start -= datetime.timedelta(hours=24)
    end = start + datetime.timedelta(hours=24)
    return [entry for entry in entries if entry[1] > start and entry[1] < end]


def entries_to_intervals(entries):
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
        intervals.append(datetime.datetime.now() - start)
    return [interval.seconds for interval in intervals]


def seconds_to_hours_and_minutes(seconds):
    hours = math.floor(seconds / 3600)
    minutes = math.floor((seconds / 60) % 60)
    return (hours, minutes)


def print_report():
    path = locate_timesheet()
    all_entries = load_timesheet(path)
    todays_entries = filter_todays_entries(all_entries)
    intervals = entries_to_intervals(todays_entries)
    seconds_worked = sum(intervals, 0)
    hours, minutes = seconds_to_hours_and_minutes(seconds_worked)
    seconds_left = WORKDAY_SECONDS - seconds_worked
    end_of_day = datetime.datetime.now() + datetime.timedelta(seconds=seconds_left)

    print()
    for entry in todays_entries:
        print("{0:5s} {1}".format(entry[0], entry[1].strftime("%T")))
    print()
    print("Worked today:     {0:.0f} hours {1:.0f} minutes".format(
        hours, minutes))
    print("End of work day:  {0}".format(end_of_day.strftime("%Hh%M")))
    print()


def new_entry(type):
    with open(locate_timesheet(), "a") as timesheet:
        timestamp = datetime.datetime.now().strftime("%c")
        timesheet.write(timestamp + " " + type + "\n")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print_report()
    elif len(sys.argv) > 2 or sys.argv[1] not in ("in", "out"):
        print_usage()
    else:
        new_entry(sys.argv[1])
