import os
import datetime
import math
import subprocess

WORKDAY_START_TIME = datetime.time(6, 0, 0)
WORKDAY_SECONDS = 8 * 60 * 60
DAILY_HISTORY_LENGTH = datetime.timedelta(days=18)
WEEKLY_HISTORY_LENGTH = datetime.timedelta(days=70)
TIMESTAMP_FORMAT = "%Y/%m/%d %Hh%M"
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def locate_timesheet():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "..", "timesheet.txt")


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
    return filter_entries(entries, start, end)


def filter_entries(entries, after, before=datetime.datetime.now()):
    return [entry for entry in entries if entry[1] > after and entry[1] < before]


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
        ref = start.replace(minute=0, second=0, microsecond=0)
        slicemap[ref] = slicemap.get(ref, 0) + (end - start).seconds
    consolidated = []
    for ref, duration in slicemap.items():
        consolidated.append((ref, ref + datetime.timedelta(seconds=duration)))
    return consolidated


def consolidate_slices_by_day(slices):
    slicemap = {}
    for slice in slices:
        start, end = slice
        ref = start.replace(hour=WORKDAY_START_TIME.hour,
                            minute=WORKDAY_START_TIME.minute,
                            second=0, microsecond=0)
        if start.time() < WORKDAY_START_TIME:
            ref -= datetime.timedelta(hours=24)
        slicemap[ref] = slicemap.get(ref, 0) + (end - start).seconds
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
    return hours


def group_slices_by_weekday(slices):
    days = [[] for i in range(7)]
    for slice in slices:
        start, end = slice
        day = start.weekday()
        time = start.time()
        if time < WORKDAY_START_TIME:
            day = 6 if day == 0 else day - 1
        days[day].append((end - start).seconds)
    return days


def group_slices_by_week(slices):
    weekmap = {}
    for slice in slices:
        start, end = slice
        week = start.isocalendar()[1]
        value = weekmap.get(week, (0, set()))
        value = (value[0] + (end - start).seconds, value[1])
        if start.weekday() < 5:
            value[1].add(start.weekday())
        weekmap[week] = value
    return weekmap


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


def render_bargraph(values, labels, bounds, w, h):
    canvas = [[" " for i in range(w)] for j in range(h)]
    min_value = bounds[0]
    max_value = bounds[1]
    diff = max(1, max_value - min_value)
    normalized = [(value - min_value) / diff for value in values]
    bar_w = int(w / len(values))
    for bar, value in enumerate(normalized):
        bar_h = int(value * h)
        for j in range(min(bar_h, h)):
            for i in range(max(1, bar_w - 1)):
                canvas[j][bar * bar_w + i] = u"\u2588"
    labelline = ["{0:<{1}}".format(label, bar_w) for label in labels]
    labelline += [" "] * (w - len("".join(labelline)))
    canvas.insert(0, labelline)
    canvas.insert(0, ["-" for i in range(w)])
    canvas.insert(2, ["-" for i in range(w)])
    canvas.append(["-" for i in range(w)])
    for i, line in enumerate(canvas):
        c = "|"
        if i in (0, len(canvas) - 1):
            c = "+"
        line.insert(0, c)
        line.append(c)
    return reversed(canvas)


def print_bargraph(graph):
    for row in graph:
        print("".join(row))


def print_hourly_histogram():
    path = locate_timesheet()
    all_entries = load_timesheet(path)
    if len(all_entries) == 0:
        print("No data available")
        return
    intervals = entries_to_intervals(all_entries)
    slices = slice_intervals_by_hour(intervals)
    hourly_history = consolidate_slices_by_hour(slices)
    daily_history = consolidate_slices_by_day(hourly_history)
    daily_histogram = group_slices_by_weekday(daily_history)
    num_days = sum([len(d) for d in daily_histogram])
    hourly_histogram = group_slices_by_hour(hourly_history)
    hourly_histogram_norm = [sum(h) / num_days for h in hourly_histogram]
    labels = ["{:02d}".format(i) for i in range(24)]
    rotated_values = hourly_histogram_norm[6:] + hourly_histogram_norm[:6]
    rotated_labels = labels[6:] + labels[:6]
    graph = render_bargraph(rotated_values, rotated_labels,
                            (0, 3600), 96, 12)
    print_bargraph(graph)


def print_daily_histogram():
    path = locate_timesheet()
    all_entries = load_timesheet(path)
    if len(all_entries) == 0:
        print("No data available")
        return
    intervals = entries_to_intervals(all_entries)
    slices = slice_intervals_by_hour(intervals)
    daily_history = consolidate_slices_by_day(slices)
    if daily_history[-1][0].date() == datetime.datetime.now().date():
        daily_history.pop()  # discard today's data as incomplete
    daily_histogram = group_slices_by_weekday(daily_history)
    daily_histogram_norm = [
        sum(d) / len(d) if len(d) > 0 else 0 for d in daily_histogram]
    graph = render_bargraph(daily_histogram_norm,
                            ["{} ({})".format(WEEKDAYS[i], len(daily_histogram[i]))
                             for i in range(7)],
                            (0, WORKDAY_SECONDS), 96, 12)
    print_bargraph(graph)


def print_recent_history():
    path = locate_timesheet()
    all_entries = load_timesheet(path)
    if len(all_entries) == 0:
        print("No data available")
        return
    intervals = entries_to_intervals(all_entries)
    slices = slice_intervals_by_hour(intervals)
    history = consolidate_slices_by_day(slices)
    history_start = datetime.datetime.now() - DAILY_HISTORY_LENGTH
    recent_history = filter_entries(history, history_start)
    values = [(t[1] - t[0]).seconds for t in recent_history]
    labels = ["{} {:02d}".format(
        WEEKDAYS[t[0].weekday()][:2], t[0].day) for t in recent_history]
    graph = render_bargraph(values, labels, (0, WORKDAY_SECONDS), 96, 12)
    print_bargraph(graph)


def print_history_by_week():
    path = locate_timesheet()
    all_entries = load_timesheet(path)
    if len(all_entries) == 0:
        print("No data available")
        return
    intervals = entries_to_intervals(all_entries)
    slices = slice_intervals_by_hour(intervals)
    history = consolidate_slices_by_day(slices)
    history_start = datetime.datetime.now() - WEEKLY_HISTORY_LENGTH
    recent_history = filter_entries(history, history_start)
    weekly = group_slices_by_week(recent_history)
    weekly_time = [time for time, _ in weekly.values()]
    weekly_labels = ["{} ({})".format(key, len(value[1]))
                     for key, value in weekly.items()]
    graph = render_bargraph(weekly_time, weekly_labels,
                            (0, WORKDAY_SECONDS * 5), 96, 12)
    print_bargraph(graph)


def new_entry(type):
    with open(locate_timesheet(), "a") as timesheet:
        timestamp = datetime.datetime.now().strftime(TIMESTAMP_FORMAT)
        timesheet.write(timestamp + " " + type + "\n")


def undo_last_entry():
    path = locate_timesheet()
    all_entries = load_timesheet(path)
    if len(all_entries) > 0:
        all_entries = all_entries[:-1]
        with open(path, "w") as timesheet:
            for entry in all_entries:
                print("{} {}".format(entry[1].strftime(TIMESTAMP_FORMAT), entry[0]), file=timesheet)


def validate_timesheet():
    path = locate_timesheet()
    all_entries = load_timesheet(path)
    expected_type = "in"
    for (type, timestamp) in all_entries:
        if type != expected_type:
            print("Error in entry {}: expected type '{}', got '{}'".format(
                timestamp, expected_type, type))
            return
        expected_type = "out" if expected_type == "in" else "in"
    print("No errors")
