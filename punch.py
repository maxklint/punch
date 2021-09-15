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
    starts = []
    ends = []
    start = None
    for entry in entries:
        if entry[0] == "in":
            if not start:
                start = entry[1]
                starts.append(start)
        elif entry[0] == "out":
            if start:
                ends.append(entry[1])
                start = None
    if start:
        ends.append(datetime.datetime.now())
    return zip(starts, ends)


def intervals_to_durations(intervals):
    durations = []
    for interval in intervals:
        durations.append((interval[1] - interval[0]).seconds)
    return durations


def seconds_to_hours_and_minutes(seconds):
    hours = math.floor(seconds / 3600)
    minutes = math.floor((seconds / 60) % 60)
    return (hours, minutes)


def slice_interval_by_hour(interval):
    slices = []
    start, end = interval
    ref = datetime.datetime(start.year, start.month, start.day, start.hour)
    while ref < end:
        remaining = min((end - ref).seconds, 3600)
        if ref < start:
            remaining -= (start - ref).seconds
        slices.append((ref, ref + datetime.timedelta(seconds=remaining)))
        ref += datetime.timedelta(hours=1)
    return slices


def slice_intervals_by_hour(intervals):
    slices = []
    for interval in intervals:
        slices.extend(slice_interval_by_hour(interval))
    return slices


def consolidate_slices_by_hour(slices):
    slicemap = {}
    for slice in slices:
        start, end = slice
        slicemap[start] = slicemap.get(start, 0) + (end - start).seconds
    consolidated = []
    for ref, duration in slicemap.items():
        consolidated.append((ref, ref + datetime.timedelta(seconds=duration)))
    return consolidated


def group_slices_by_hour(slices):
    hours = [[] for i in range(24)]
    for slice in slices:
        start, end = slice
        hour = start.hour
        hours[hour].append((end - start).seconds)
    for hour in hours:
        if len(hour) == 0:
            hour.append(0)
    return hours


def print_overview():
    path = locate_timesheet()
    all_entries = load_timesheet(path)
    todays_entries = filter_todays_entries(all_entries)
    intervals = entries_to_intervals(todays_entries)
    durations = intervals_to_durations(intervals)
    seconds_worked = sum(durations, 0)
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


def render_bargraph(values, w, h):
    canvas = [[" " for i in range(w)] for j in range(h)]
    max_value = max(values)
    min_value = min(values)
    diff = max(1, max_value - min_value)
    normalized = [(value - min_value) / diff for value in values]
    bar_w = int(w / len(values))
    for bar, value in enumerate(normalized):
        bar_h = int(value * h)
        for j in range(bar_h):
            for i in range(max(1, bar_w - 1)):
                canvas[j][bar * bar_w + i] = u"\u2588"
    canvas.insert(0, ["{0:<{1}}".format(x, bar_w) for x in range(len(values))])
    return reversed(canvas)


def print_stats():
    path = locate_timesheet()
    all_entries = load_timesheet(path)
    intervals = entries_to_intervals(all_entries)
    slices = slice_intervals_by_hour(intervals)
    consolidated = consolidate_slices_by_hour(slices)
    hourly = group_slices_by_hour(consolidated)
    hourly_avg = [sum(h) for h in hourly]
    graph = render_bargraph(hourly_avg, 80, 12)
    for row in graph:
        print("".join(row))


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
    elif sys.argv[1] == "stats":
        print_stats()
    else:
        print_usage()
