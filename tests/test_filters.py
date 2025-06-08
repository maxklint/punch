import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import datetime

import punch


def test_filter_entries_within_range():
    after = datetime.datetime(2024, 1, 15, 6, 0)
    before = datetime.datetime(2024, 1, 15, 9, 0)
    entries = [
        ("in", datetime.datetime(2024, 1, 15, 5, 59)),
        ("in", datetime.datetime(2024, 1, 15, 6, 0, 1)),
        ("out", datetime.datetime(2024, 1, 15, 8, 30)),
        ("out", datetime.datetime(2024, 1, 15, 9, 1)),
    ]
    assert punch.filter_entries(entries, after, before) == entries[1:3]


def test_filter_todays_entries(monkeypatch):
    fixed_now = datetime.datetime(2024, 1, 15, 15, 30)

    class FixedDatetime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now.replace(tzinfo=tz)

    monkeypatch.setattr(punch.datetime, "datetime", FixedDatetime)

    entries = [
        ("in", datetime.datetime(2024, 1, 14, 7, 0)),
        ("out", datetime.datetime(2024, 1, 15, 7, 0)),
        ("in", datetime.datetime(2024, 1, 15, 12, 0)),
        ("out", datetime.datetime(2024, 1, 16, 5, 59)),
        ("in", datetime.datetime(2024, 1, 16, 6, 1)),
    ]

    assert punch.filter_todays_entries(entries) == entries[1:4]
