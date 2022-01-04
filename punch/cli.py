from . import *
import click


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Simple command-line time tracker."""
    if ctx.invoked_subcommand is None:
        print_overview()


@cli.command(name="in")
def entry_in():
    """Add new 'in' entry"""
    new_entry("in")


@cli.command(name="out")
def entry_out():
    """Add new 'out' entry"""
    new_entry("out")

@cli.command()
def undo():
    """Undo last entry"""
    undo_last_entry()

@cli.command()
def check():
    """Validate timesheet"""
    validate_timesheet()


@cli.command()
def edit():
    """Open timesheet in text editor"""
    open_timesheet_in_editor()


@cli.command()
def hourly():
    """Print statistics by hour"""
    print_hourly_histogram()


@cli.command()
def daily():
    """Print statistics by day"""
    print_daily_histogram()


@cli.command()
def weekly():
    """Print statistics by week"""
    print_history_by_week()


@cli.command()
def history():
    """Print recent history"""
    print_recent_history()
