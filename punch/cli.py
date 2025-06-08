from . import *
from . import __version__
import click
import datetime


class TimestampType(click.ParamType):
    name = "timestamp"

    def convert(self, value, param, ctx):
        if value == "":
            return datetime.datetime.now()

        date = datetime.date.today()
        for format in ["%Hh%M", "%H:%M"]:
            try:
                time = datetime.datetime.strptime(value, format)
                timestamp = datetime.datetime(
                    year=date.year,
                    month=date.month,
                    day=date.day,
                    hour=time.hour,
                    minute=time.minute,
                    second=time.second,
                )
                return timestamp
            except:
                pass

        self.fail("{} is not a valid timestamp".format(value), param, ctx)


timestamp_argument = click.argument("timestamp", type=TimestampType(), default="")

file_option = click.option(
    "-f",
    "--file",
    "path",
    required=True,
    envvar="PUNCH_TIMESHEET",
    type=click.Path(),
    help="Path to timesheet file",
)


@click.group(invoke_without_command=True, add_help_option=False)
@file_option
@click.pass_context
@click.help_option()
@click.version_option(__version__)
def cli(ctx, path):
    """Simple command-line time tracker."""
    if ctx.invoked_subcommand is None:
        print_overview(path)


@cli.command(name="in")
@file_option
@timestamp_argument
def entry_in(path, timestamp):
    """Add new 'in' entry"""
    new_entry(path, timestamp, "in")


@cli.command(name="out")
@file_option
@timestamp_argument
def entry_out(path, timestamp):
    """Add new 'out' entry"""
    new_entry(path, timestamp, "out")


@cli.command()
@file_option
def undo(path):
    """Undo last entry"""
    undo_last_entry(path)


@cli.command()
@file_option
def check(path):
    """Validate timesheet"""
    validate_timesheet(path)


@cli.command()
@file_option
def edit(path):
    """Open timesheet in text editor"""
    open_timesheet_in_editor(path)


@cli.command()
@file_option
def hourly(path):
    """Print statistics by hour"""
    print_hourly_histogram(path)


@cli.command()
@file_option
def daily(path):
    """Print statistics by day"""
    print_daily_histogram(path)


@cli.command()
@file_option
def weekly(path):
    """Print statistics by week"""
    print_history_by_week(path)


@cli.command()
@file_option
def history(path):
    """Print recent history"""
    print_recent_history(path)


@cli.command()
@file_option
@click.argument("output", type=click.Path())
def export(path, output):
    """Export timesheet to JSON"""
    export_entries_to_json(path, output)


@cli.command()
@file_option
@click.argument("year", type=click.INT)
def total(path, year):
    """Print total hours for the given year"""
    start = datetime.datetime(year, 1, 1)
    end = datetime.datetime(year + 1, 1, 1)
    print_total_hours_for_period(path, start, end)
