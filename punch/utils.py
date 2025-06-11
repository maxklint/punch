import datetime
import math
from . import config


def workday_start_for(
    timestamp: datetime.datetime, workday_start: datetime.time
) -> datetime.datetime:
    """
    Given a datetime `timestamp`, return the datetime corresponding to the start of the
    workday it belongs to.
    """
    if timestamp.time() < workday_start:
        return datetime.datetime.combine(
            timestamp.date(), workday_start
        ) - datetime.timedelta(days=1)
    return datetime.datetime.combine(timestamp.date(), workday_start)


def filter_todays_entries(entries):
    now = datetime.datetime.now()
    start = datetime.datetime(
        now.year,
        now.month,
        now.day,
        config.WORKDAY_START_TIME.hour,
        config.WORKDAY_START_TIME.minute,
    )
    if now.time() < config.WORKDAY_START_TIME:
        start -= datetime.timedelta(hours=24)
    end = start + datetime.timedelta(hours=24)
    return filter_entries(entries, start, end)


def filter_entries(entries, after, before=None):
    if before is None:
        before = datetime.datetime.now()
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
        ref = start.replace(
            hour=config.WORKDAY_START_TIME.hour,
            minute=config.WORKDAY_START_TIME.minute,
            second=0,
            microsecond=0,
        )
        if start.time() < config.WORKDAY_START_TIME:
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
        if time < config.WORKDAY_START_TIME:
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
