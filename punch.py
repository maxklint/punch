import sys
import datetime


TIMESHEET_PATH = "/Users/aimmx/Documents/Code/utils/punch/timesheet.txt"


def print_usage():
    print("USAGE: punch in|out")


def punch(state):
    with open(TIMESHEET_PATH, "a") as timesheet:
        timestamp = datetime.datetime.now().strftime("%c")
        timesheet.write("[" + timestamp + "] " + state + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("in", "out"):
        print_usage()
    else:
        punch(sys.argv[1])
