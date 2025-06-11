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
