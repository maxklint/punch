import datetime
import json
import os
import subprocess
from . import config, graph, timesheet, utils


def print_overview(path):
    all_entries = timesheet.load_timesheet(path)
    todays_entries = utils.filter_todays_entries(all_entries)
    intervals = utils.entries_to_intervals(todays_entries)
    durations = utils.intervals_to_durations(intervals)
    seconds_worked = sum(durations, 0)
    hours, minutes = utils.seconds_to_hours_and_minutes(seconds_worked)
    seconds_left = config.WORKDAY_SECONDS - seconds_worked
    end_of_day = datetime.datetime.now() + datetime.timedelta(seconds=seconds_left)

    print()
    for entry in todays_entries:
        print("{0:5s} {1}".format(entry[0], entry[1].strftime("%Hh%M")))
    print()
    print("Worked today:     {0:.0f} hours {1:.0f} minutes".format(hours, minutes))
    print("End of work day:  {0}".format(end_of_day.strftime("%Hh%M")))
    print()


def new_entry(path, timestamp, type):
    all_entries = timesheet.load_timesheet(path)
    if len(all_entries) > 0:
        last_type, last_timestamp = all_entries[-1]
        if last_type == type:
            print(
                "Error: last entry was '{}' at {}".format(
                    last_type, last_timestamp.strftime(config.TIMESTAMP_FORMAT)
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
                        entry[1].strftime(config.TIMESTAMP_FORMAT), entry[0]
                    ),
                    file=ofile,
                )


def validate_timesheet(path):
    all_entries = timesheet.load_timesheet(path)
    expected_type = "in"
    for type, timestamp in all_entries:
        if type != expected_type:
            print(
                "Error in entry {}: expected type '{}', got '{}'".format(
                    timestamp, expected_type, type
                )
            )
            return
        expected_type = "out" if expected_type == "in" else "in"
    print("No errors")


def open_timesheet_in_editor(path):
    editor = os.getenv("EDITOR", "vim")
    subprocess.call([editor, path])


def print_hourly_histogram(path):
    all_entries = timesheet.load_timesheet(path)
    if len(all_entries) == 0:
        print("No data available")
        return
    intervals = utils.entries_to_intervals(all_entries)
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
    slices = utils.slice_intervals_by_hour(intervals)
    daily_history = utils.consolidate_slices_by_day(slices)
    if daily_history[-1][0].date() == datetime.datetime.now().date():
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
    slices = utils.slice_intervals_by_hour(intervals)
    history = utils.consolidate_slices_by_day(slices)
    history_start = datetime.datetime.now() - config.DAILY_HISTORY_LENGTH
    recent_history = utils.filter_entries(history, history_start)
    values = [(t[1] - t[0]).seconds for t in recent_history]
    labels = [
        "{} {:02d}".format(config.WEEKDAYS[t[0].weekday()][:2], t[0].day)
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
    slices = utils.slice_intervals_by_hour(intervals)
    history = utils.consolidate_slices_by_day(slices)
    history_start = datetime.datetime.now() - config.WEEKLY_HISTORY_LENGTH
    recent_history = utils.filter_entries(history, history_start)
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
    slices = utils.slice_intervals_by_hour(intervals)
    history = utils.consolidate_slices_by_day(slices)
    selected_history = utils.filter_entries(history, history_start, history_end)
    values = [(t[1] - t[0]).seconds for t in selected_history]
    print("{}h".format(round(sum(values) / 3600.0)))


def export_entries_to_json(path, output_path):
    if os.path.exists(output_path):
        print(f"Error: {output_path} already exists")
        return
    entries = timesheet.load_timesheet(path)
    data = [
        {"timestamp": timestamp.strftime(config.TIMESTAMP_FORMAT), "type": type}
        for type, timestamp in entries
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
        entries.append((item["type"], timestamp))

    with open(path, "w") as outfile:
        for type, timestamp in entries:
            outfile.write(f"{timestamp.strftime(config.TIMESTAMP_FORMAT)} {type}\n")

    validate_timesheet(path)
