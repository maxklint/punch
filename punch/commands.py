import datetime
import json
import os
import subprocess
from . import config, graph, timesheet, utils


def print_overview(path):
    all_entries = timesheet.load_timesheet(path)
    intervals = utils.entries_to_intervals(all_entries)
    todays_intervals = utils.filter_intervals(intervals, utils.start_of_today())
    seconds_worked_today = 0
    seconds_not_worked_today = 0
    prev_end = None
    for interval in todays_intervals:
        end = (
            interval.timestamp + interval.duration
            if interval.duration
            else datetime.datetime.now()
        )
        seconds_worked_today += (end - interval.timestamp).seconds
        if prev_end is not None:
            seconds_not_worked_today += (interval.timestamp - prev_end).seconds
        prev_end = end

    todays_breaks = max(0, len(todays_intervals) - 1)

    weeks_intervals = utils.filter_intervals(intervals, utils.start_of_week())
    seconds_worked_this_week = 0
    for interval in weeks_intervals:
        if interval.duration is not None:
            seconds_worked_this_week += interval.duration.seconds
        else:
            seconds_worked_this_week += (
                datetime.datetime.now() - interval.timestamp
            ).seconds

    print()
    for interval in todays_intervals:
        print(f"in    {interval.timestamp.strftime('%Hh%M')}")
        if interval.duration is not None:
            print(f"out   {(interval.timestamp + interval.duration).strftime('%Hh%M')}")
    print()
    print(
        "Worked today:     {0:.0f} hours {1:.0f} minutes".format(
            *utils.seconds_to_hours_and_minutes(seconds_worked_today)
        )
    )
    print(
        "Total break time: {0:.0f} hours {1:.0f} minutes ({2} break{3})".format(
            *utils.seconds_to_hours_and_minutes(seconds_not_worked_today),
            todays_breaks,
            "" if todays_breaks == 1 else "s",
        )
    )
    print()
    print(
        "Worked this week: {0:.0f} hours {1:.0f} minutes".format(
            *utils.seconds_to_hours_and_minutes(seconds_worked_this_week)
        )
    )
    print()


def new_entry(path, timestamp, type):
    all_entries = timesheet.load_timesheet(path)
    if len(all_entries) > 0:
        last_entry = all_entries[-1]
        if last_entry.type == type:
            print(
                "Error: last entry was '{}' at {}".format(
                    last_entry.type,
                    last_entry.timestamp.strftime(config.TIMESTAMP_FORMAT),
                )
            )
            return
    with open(path, "a") as ofile:
        ofile.write(timestamp.strftime(config.TIMESTAMP_FORMAT) + " " + type + "\n")


def undo_last_entry(path):
    all_entries = timesheet.load_timesheet(path)
    if len(all_entries) > 0:
        all_entries = all_entries[:-1]
        with open(path, "w") as ofile:
            for entry in all_entries:
                print(
                    "{} {}".format(
                        entry.timestamp.strftime(config.TIMESTAMP_FORMAT),
                        entry.type,
                    ),
                    file=ofile,
                )


def validate_timesheet(path):
    try:
        timesheet.load_timesheet(path)
        print("No errors")
    except ValueError as e:
        print(str(e))


def open_timesheet_in_editor(path):
    editor = os.getenv("EDITOR", "vim")
    subprocess.call([editor, path])


def print_hourly_histogram(path):
    all_entries = timesheet.load_timesheet(path)
    if len(all_entries) == 0:
        print("No data available")
        return
    intervals = utils.entries_to_intervals(all_entries)
    if intervals[-1].duration is None:
        intervals[-1] = utils.Interval(
            timestamp=intervals[-1].timestamp,
            duration=datetime.datetime.now() - intervals[-1].timestamp,
        )
    slices = utils.slice_intervals_by_hour(intervals)
    hourly_history = utils.consolidate_slices_by_hour(slices)
    daily_history = utils.consolidate_slices_by_day(hourly_history)
    daily_histogram = utils.group_slices_by_weekday(daily_history)
    num_days = sum([len(d) for d in daily_histogram])
    hourly_histogram = utils.group_slices_by_hour(hourly_history)
    hourly_histogram_norm = [sum(h) / num_days for h in hourly_histogram]
    labels = ["{:02d}".format(i) for i in range(24)]
    rotated_values = hourly_histogram_norm[6:] + hourly_histogram_norm[:6]
    rotated_labels = labels[6:] + labels[:6]
    graph_data = graph.render_bargraph(
        rotated_values, rotated_labels, (0, 3600), 96, 12
    )
    graph.print_bargraph(graph_data)


def print_daily_histogram(path):
    all_entries = timesheet.load_timesheet(path)
    if len(all_entries) == 0:
        print("No data available")
        return
    intervals = utils.entries_to_intervals(all_entries)
    if intervals[-1].duration is None:
        intervals[-1] = utils.Interval(
            timestamp=intervals[-1].timestamp,
            duration=datetime.datetime.now() - intervals[-1].timestamp,
        )
    slices = utils.slice_intervals_by_hour(intervals)
    daily_history = utils.consolidate_slices_by_day(slices)
    if daily_history[-1].timestamp.date() == datetime.datetime.now().date():
        daily_history.pop()  # discard today's data as incomplete
    daily_histogram = utils.group_slices_by_weekday(daily_history)
    daily_histogram_norm = [
        sum(d) / len(d) if len(d) > 0 else 0 for d in daily_histogram
    ]
    graph_data = graph.render_bargraph(
        daily_histogram_norm,
        [
            "{} ({})".format(config.WEEKDAYS[i], len(daily_histogram[i]))
            for i in range(7)
        ],
        (0, config.WORKDAY_SECONDS),
        96,
        12,
    )
    graph.print_bargraph(graph_data)


def print_recent_history(path):
    all_entries = timesheet.load_timesheet(path)
    if len(all_entries) == 0:
        print("No data available")
        return
    intervals = utils.entries_to_intervals(all_entries)
    if intervals[-1].duration is None:
        intervals[-1] = utils.Interval(
            timestamp=intervals[-1].timestamp,
            duration=datetime.datetime.now() - intervals[-1].timestamp,
        )
    slices = utils.slice_intervals_by_hour(intervals)
    history = utils.consolidate_slices_by_day(slices)
    history_start = datetime.datetime.now() - config.DAILY_HISTORY_LENGTH
    recent_history = utils.filter_intervals(history, history_start)
    values = [t.duration.seconds for t in recent_history]
    labels = [
        "{} {:02d}".format(config.WEEKDAYS[t.timestamp.weekday()][:2], t.timestamp.day)
        for t in recent_history
    ]
    graph_data = graph.render_bargraph(
        values, labels, (0, config.WORKDAY_SECONDS), 96, 12
    )
    graph.print_bargraph(graph_data)


def print_history_by_week(path):
    all_entries = timesheet.load_timesheet(path)
    if len(all_entries) == 0:
        print("No data available")
        return
    intervals = utils.entries_to_intervals(all_entries)
    if intervals[-1].duration is None:
        intervals[-1] = utils.Interval(
            timestamp=intervals[-1].timestamp,
            duration=datetime.datetime.now() - intervals[-1].timestamp,
        )
    slices = utils.slice_intervals_by_hour(intervals)
    history = utils.consolidate_slices_by_day(slices)
    history_start = datetime.datetime.now() - config.WEEKLY_HISTORY_LENGTH
    recent_history = utils.filter_intervals(history, history_start)
    weekly = utils.group_slices_by_week(recent_history)
    weekly_time = [time for time, _ in weekly.values()]
    weekly_labels = [
        "{} ({})".format(key, len(value[1])) for key, value in weekly.items()
    ]
    graph_data = graph.render_bargraph(
        weekly_time, weekly_labels, (0, config.WORKDAY_SECONDS * 5), 96, 12
    )
    graph.print_bargraph(graph_data)


def print_total_hours_for_period(path, history_start, history_end):
    all_entries = timesheet.load_timesheet(path)
    if len(all_entries) == 0:
        print("No data available")
        return
    intervals = utils.entries_to_intervals(all_entries)
    if intervals[-1].duration is None:
        intervals[-1] = utils.Interval(
            timestamp=intervals[-1].timestamp,
            duration=datetime.datetime.now() - intervals[-1].timestamp,
        )
    slices = utils.slice_intervals_by_hour(intervals)
    history = utils.consolidate_slices_by_day(slices)
    selected_history = utils.filter_intervals(history, history_start, history_end)
    values = [t.duration.seconds for t in selected_history]
    print("{}h".format(round(sum(values) / 3600.0)))


def export_entries_to_json(path, output_path):
    if os.path.exists(output_path):
        print(f"Error: {output_path} already exists")
        return
    entries = timesheet.load_timesheet(path)
    data = [
        {
            "timestamp": entry.timestamp.strftime(config.TIMESTAMP_FORMAT),
            "type": entry.type,
        }
        for entry in entries
    ]
    with open(output_path, "w") as ofile:
        json.dump(data, ofile, indent=2)


def import_entries_from_json(path, input_path):
    if os.path.exists(path):
        print(f"Error: {path} already exists")
        return
    with open(input_path, "r") as ifile:
        try:
            data = json.load(ifile)
        except Exception:
            print(f"Error: could not load {input_path}")
            return

    entries = []
    for item in data:
        if not isinstance(item, dict) or "timestamp" not in item or "type" not in item:
            print("Error: invalid entry in JSON file")
            return
        try:
            timestamp = datetime.datetime.strptime(
                item["timestamp"], config.TIMESTAMP_FORMAT
            )
        except Exception:
            print(f"Error: invalid timestamp '{item.get('timestamp')}'")
            return
        if item["type"] not in ("in", "out"):
            print(f"Error: invalid type '{item['type']}'")
            return
        entries.append(timesheet.Entry(type=item["type"], timestamp=timestamp))

    with open(path, "w") as outfile:
        for entry in entries:
            outfile.write(
                f"{entry.timestamp.strftime(config.TIMESTAMP_FORMAT)} {entry.type}\n"
            )

    try:
        entries = timesheet.load_timesheet(path)
        print(f"Successfully imported {len(entries)} entries")
    except ValueError as e:
        print(str(e))
