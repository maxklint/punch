import datetime


WORKDAY_START_TIME = datetime.time(6, 0, 0)
WORKDAY_SECONDS = 8 * 60 * 60
DAILY_HISTORY_LENGTH = datetime.timedelta(days=18)
WEEKLY_HISTORY_LENGTH = datetime.timedelta(days=70)
TIMESTAMP_FORMAT = "%Y/%m/%d %Hh%M"
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
