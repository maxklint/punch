import os
import sys
import datetime
import math
import subprocess

WORKDAY_START_TIME = datetime.time(6, 0, 0)
WORKDAY_SECONDS = 8 * 60 * 60
TIMESTAMP_FORMAT = "%Y/%m/%d %Hh%M"


def print_usage():
    print("USAGE: punch [in | out]")


def locate_timesheet():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "timesheet.txt")


def open_timesheet_in_editor():
    editor = os.getenv("EDITOR", "vim")
    subprocess.call([editor, locate_timesheet()])


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
                timestamp = datetime.datetime.strptime(line, TIMESTAMP_FORMAT)
            except:
                print("error")
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
    starts = []
    start = None
    for entry in entries:
        if entry[0] == "in":
            if not start:
                start = entry[1]
                starts.append(start)
        elif entry[0] == "out":
            if start:
                intervals.append(entry[1] - start)
                start = None
    if start:
        intervals.append(datetime.datetime.now() - start)
    seconds = [interval.seconds for interval in intervals]
    return seconds, starts


def seconds_to_hours_and_minutes(seconds):
    hours = math.floor(seconds / 3600)
    minutes = math.floor((seconds / 60) % 60)
    return (hours, minutes)


def split_by_hour(start, end):
    blocks = []
    reference = datetime.datetime(
        start.year, start.month, start.day, start.hour)
    while reference < end:
        remaining = min((end - reference).seconds, 3600)
        if reference < start:
            remaining -= (start - reference).seconds
        blocks.append((reference, remaining))
        reference += datetime.timedelta(hours=1)
    return blocks


def print_overview():
    path = locate_timesheet()
    all_entries = load_timesheet(path)
    todays_entries = filter_todays_entries(all_entries)
    intervals, _ = entries_to_intervals(todays_entries)
    seconds_worked = sum(intervals, 0)
    hours, minutes = seconds_to_hours_and_minutes(seconds_worked)
    seconds_left = WORKDAY_SECONDS - seconds_worked
    end_of_day = datetime.datetime.now() + datetime.timedelta(seconds=seconds_left)

    print()
    for entry in todays_entries:
        print("{0:5s} {1}".format(entry[0], entry[1].strftime("%Hh%M")))
    print()
    print("Worked today:     {0:.0f} hours {1:.0f} minutes".format(
        hours, minutes))
    print("End of work day:  {0}".format(end_of_day.strftime("%Hh%M")))
    print()


def print_stats():
    path = locate_timesheet()
    all_entries = load_timesheet(path)
    intervals, starts = entries_to_intervals(all_entries)
    daily = [[0] for i in range(7)]
    hourly = [[0] for i in range(24)]
    for i in range(len(intervals)):
        start = starts[i]
        interval = intervals[i]
        end = start + datetime.timedelta(seconds=interval)
        blocks = split_by_hour(start, end)
        for block in blocks:
            hour = block[0].hour
            date = block[0].date()
            if hour < WORKDAY_START_TIME.hour:
                date -= datetime.timedelta(hours=24)
            weekday = date.weekday()
            daily[weekday].append(block[1] / 3600.0)
            hourly[hour].append(block[1] / 60.0)

    daily_sum = [sum(hours) for hours in daily]
    for weekday, hours in enumerate(daily_sum):
        print("{0} | {1}".format(weekday, hours))

    # hourly_sum = [sum(hours) for hours in hourly]
    # hourly_max = max(hourly_sum)
    # hourly_norm = [h / hourly_max for h in hourly_sum]
    # for hour, norm in enumerate(hourly_norm):
    #     print("{0:02}:00 - {1:02}:00 | {2}".format(hour, hour + 1, "+" * int(40 * norm)))


def new_entry(type):
    with open(locate_timesheet(), "a") as timesheet:
        timestamp = datetime.datetime.now().strftime(TIMESTAMP_FORMAT)
        timesheet.write(timestamp + " " + type + "\n")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print_overview()
    elif sys.argv[1] in ("in", "out"):
        new_entry(sys.argv[1])
    elif sys.argv[1] == "edit":
        open_timesheet_in_editor()
    # elif sys.argv[1] == "stats":
        # print_stats()
    else:
        print_usage()
