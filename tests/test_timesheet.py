import datetime
import pytest

from punch.timesheet import Timesheet, MismatchedEntryException


def test_add_entry_invalid_type(tmp_path):
    sheet = Timesheet(str(tmp_path / "sheet.db"))
    with pytest.raises(ValueError):
        sheet.add_entry(datetime.datetime.now(), "foo")


def test_add_entry_consecutive_same_type(tmp_path):
    sheet = Timesheet(str(tmp_path / "sheet.db"))
    timestamp = datetime.datetime.now()
    sheet.add_entry(timestamp, "in")

    timestamp += datetime.timedelta(minutes=1)
    with pytest.raises(MismatchedEntryException):
        sheet.add_entry(timestamp, "in")

    timestamp += datetime.timedelta(minutes=1)
    with pytest.raises(MismatchedEntryException):
        sheet.add_entry(timestamp, "in")

    timestamp += datetime.timedelta(minutes=1)
    sheet.add_entry(timestamp, "out")

    timestamp += datetime.timedelta(minutes=1)
    with pytest.raises(MismatchedEntryException):
        sheet.add_entry(timestamp, "out")

    timestamp += datetime.timedelta(minutes=1)
    with pytest.raises(MismatchedEntryException):
        sheet.add_entry(timestamp, "out")


def test_delete_last_entry(tmp_path):
    sheet = Timesheet(str(tmp_path / "sheet.db"))
    ts = datetime.datetime.now().replace(microsecond=0)
    sheet.add_entry(ts, "in")
    ts += datetime.timedelta(minutes=1)
    sheet.add_entry(ts, "out")
    ts += datetime.timedelta(minutes=1)
    sheet.add_entry(ts, "in")

    sheet.delete_last_entry()

    sessions = sheet.get_sessions_in_range(
        ts - datetime.timedelta(minutes=3), datetime.timedelta(minutes=10)
    )
    assert len(sessions) == 1
    assert sessions[0].get_start() == ts - datetime.timedelta(minutes=2)
    assert sessions[0].get_end() == ts - datetime.timedelta(minutes=1)

    ts += datetime.timedelta(minutes=1)
    sheet.add_entry(ts, "in")

    sessions = sheet.get_sessions_in_range(
        ts - datetime.timedelta(minutes=4), datetime.timedelta(minutes=10)
    )
    assert len(sessions) == 2
    assert sessions[0].get_start() == ts - datetime.timedelta(minutes=3)
    assert sessions[0].get_end() == ts - datetime.timedelta(minutes=2)
    assert sessions[1].get_start() == ts
    assert sessions[1].get_end() is None


def test_delete_last_entry_no_entries(tmp_path):
    sheet = Timesheet(str(tmp_path / "sheet.db"))
    sheet.delete_last_entry()
    sessions = sheet.get_sessions_in_range(
        datetime.datetime.now() - datetime.timedelta(hours=1),
        datetime.timedelta(hours=2),
    )
    assert sessions == []

