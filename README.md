# Punch

Punch is a lightweight command line tool for tracking work time.
Entries are stored in a plain text timesheet.

## Installation

Install the package from the repository using `pip`:

```bash
pip install -e .
```

This will install a `punch` command.

## Usage

A timesheet is a text file where each line contains a timestamp
(`YYYY/MM/DD HHhMM`) followed by either `in` or `out`:

```
2023/12/15 09h00 in
2023/12/15 12h00 out
```

Use the `-f`/`--file` option or the `PUNCH_TIMESHEET` environment variable
to point the tool at the timesheet file.

### Commands

- `punch in [TIME]` – add an *in* entry (default: now)
- `punch out [TIME]` – add an *out* entry
- `punch undo` – remove the last entry
- `punch history` – show recent history
- `punch hourly` – histogram of hours of the day
- `punch daily` – histogram of days of the week
- `punch weekly` – histogram by ISO week
- `punch total YEAR` – total hours for a given year
- `punch export FILE` – export timesheet to JSON
- `punch import FILE` – import timesheet from JSON

Running `punch` with no subcommand prints an overview of today's work.
Punch assumes an 8‑hour workday starting at 06:00. The `punch hourly`,
`daily`, and `weekly` commands print ASCII bar graphs showing when you work.

## Example

First point Punch at a timesheet and record a day of work:

```bash
export PUNCH_TIMESHEET=~/work.time
punch in 09h00
punch out 12h00
punch in 13h00
punch out 17h30
```

Then view an overview or weekly statistics:

```bash
punch        # today's summary
punch weekly # bar graph of the week
```

