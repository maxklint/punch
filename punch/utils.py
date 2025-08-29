import datetime
from dataclasses import dataclass
import math
from . import config, timesheet


@dataclass(frozen=True)
class Interval:
    timestamp: datetime.datetime
    duration: datetime.timedelta


def entries_to_intervals(entries: list[timesheet.Entry]) -> list[Interval]:
    intervals = []
    timestamp = None
    for entry in entries:
        if entry.type == "in":
            timestamp = entry.timestamp
        elif entry.type == "out":
            if timestamp is None:
                raise ValueError("Mismatched 'out' entry without preceding 'in'")
            intervals.append(
                Interval(timestamp=timestamp, duration=entry.timestamp - timestamp)
            )
            timestamp = None
    if timestamp is not None:
        intervals.append(Interval(timestamp=timestamp, duration=None))
    return intervals


def start_of_today() -> datetime.datetime:
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
    return start


def start_of_week() -> datetime.datetime:
    start = start_of_today()
    start -= datetime.timedelta(days=start.weekday())
    return start


def filter_intervals(
    intervals: list[Interval],
    after: datetime.datetime,
    before: datetime.datetime = None,
) -> list[Interval]:
    if before is None:
        before = datetime.datetime.now()
    return [
        interval
        for interval in intervals
        if interval.timestamp >= after and interval.timestamp <= before
    ]


def seconds_to_hours_and_minutes(seconds: int) -> tuple[int, int]:
    hours = math.floor(seconds / 3600)
    minutes = math.floor((seconds / 60) % 60)
    return (hours, minutes)


def slice_interval_by_hour(interval: Interval) -> list[Interval]:
    slices = []
    ref = datetime.datetime(
        interval.timestamp.year,
        interval.timestamp.month,
        interval.timestamp.day,
        interval.timestamp.hour,
    )
    while ref < interval.timestamp + interval.duration:
        remaining = min(((interval.timestamp + interval.duration) - ref).seconds, 3600)
        if ref < interval.timestamp:
            remaining -= (interval.timestamp - ref).seconds
        slices.append(
            Interval(timestamp=ref, duration=datetime.timedelta(seconds=remaining))
        )
        ref += datetime.timedelta(hours=1)
    return slices


def slice_intervals_by_hour(intervals: list[Interval]) -> list[Interval]:
    slices = []
    for interval in intervals:
        slices.extend(slice_interval_by_hour(interval))
    return slices


def consolidate_slices_by_hour(slices: list[Interval]) -> list[Interval]:
    slicemap = {}
    for slice in slices:
        ref = slice.timestamp.replace(minute=0, second=0, microsecond=0)
        slicemap[ref] = slicemap.get(ref, 0) + slice.duration.seconds
    consolidated = []
    for ref, duration in slicemap.items():
        consolidated.append(
            Interval(timestamp=ref, duration=datetime.timedelta(seconds=duration))
        )
    return consolidated


def consolidate_slices_by_day(slices: list[Interval]) -> list[Interval]:
    slicemap = {}
    for slice in slices:
        ref = slice.timestamp.replace(
            hour=config.WORKDAY_START_TIME.hour,
            minute=config.WORKDAY_START_TIME.minute,
            second=0,
            microsecond=0,
        )
        if slice.timestamp.time() < config.WORKDAY_START_TIME:
            ref -= datetime.timedelta(hours=24)
        slicemap[ref] = slicemap.get(ref, 0) + slice.duration.seconds
    consolidated = []
    for ref, duration in slicemap.items():
        consolidated.append(
            Interval(timestamp=ref, duration=datetime.timedelta(seconds=duration))
        )
    return consolidated


def group_slices_by_hour(slices: list[Interval]) -> list[list[int]]:
    hours = [[] for i in range(24)]
    for slice in slices:
        hour = slice.timestamp.hour
        hours[hour].append(slice.duration.seconds)
    return hours


def group_slices_by_weekday(slices: list[Interval]) -> list[list[int]]:
    days = [[] for i in range(7)]
    for slice in slices:
        day = slice.timestamp.weekday()
        time = slice.timestamp.time()
        if time < config.WORKDAY_START_TIME:
            day = 6 if day == 0 else day - 1
        days[day].append(slice.duration.seconds)
    return days


def group_slices_by_week(slices: list[Interval]) -> dict[int, tuple[int, set[int]]]:
    weekmap = {}
    for slice in slices:
        week = slice.timestamp.isocalendar()[1]
        value = weekmap.get(week, (0, set()))
        value = (value[0] + slice.duration.seconds, value[1])
        if slice.timestamp.weekday() < 5:
            value[1].add(slice.timestamp.weekday())
        weekmap[week] = value
    return weekmap
