import datetime
from punch import utils


def test_workday_start_for():
    ws = datetime.time(6, 0)
    dt = datetime.date(2025, 6, 11)
    assert utils.workday_start_for(
        datetime.datetime.combine(dt, ws), ws
    ) == datetime.datetime.combine(dt, ws)
    assert utils.workday_start_for(
        datetime.datetime.combine(dt, ws) + datetime.timedelta(minutes=1), ws
    ) == datetime.datetime.combine(dt, ws)
    assert utils.workday_start_for(
        datetime.datetime.combine(dt, ws) - datetime.timedelta(minutes=1), ws
    ) == datetime.datetime.combine(dt - datetime.timedelta(days=1), ws)
