import os
import sys
import datetime


def print_usage():
    print("USAGE: punch in|out")


def punch(state):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "timesheet.txt")
    with open(path, "a") as timesheet:
        timestamp = datetime.datetime.now().strftime("%c")
        timesheet.write("[" + timestamp + "] " + state + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("in", "out"):
        print_usage()
    else:
        punch(sys.argv[1])
