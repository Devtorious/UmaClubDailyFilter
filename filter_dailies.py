"""
UmaClubDailyFilter
Reads a CSV club file exported from chronogenesis.net and prints the names of
club members who have NOT completed their dailies.

A member is considered to have skipped their dailies when their
"Daily Fan Gain" column value is a number strictly less than 300.
Values that contain only a dash ("-") are treated as null and are ignored.

Usage:
    python filter_dailies.py [CSV_FILE]

    CSV_FILE defaults to "sample_club_data.csv" when not provided.
"""

import csv
import sys

DAILY_FAN_THRESHOLD = 300
NULL_MARKER = "-"


def load_csv(filepath: str) -> list[dict]:
    """Return all rows from *filepath* as a list of dicts."""
    with open(filepath, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def filter_inactive_members(rows: list[dict], column: str = "Daily Fan Gain") -> list[dict]:
    """Return rows whose *column* value is a number below DAILY_FAN_THRESHOLD.

    Rows where the value equals NULL_MARKER or is otherwise non-numeric are
    skipped (treated as missing data).
    """
    inactive = []
    for row in rows:
        raw = row.get(column, "").strip()
        if raw == NULL_MARKER or raw == "":
            continue
        try:
            fan_gain = int(raw)
        except ValueError:
            continue
        if fan_gain < DAILY_FAN_THRESHOLD:
            inactive.append(row)
    return inactive


def print_report(inactive_members: list[dict], name_column: str = "Name") -> None:
    """Print a simple report of members who missed their dailies."""
    if not inactive_members:
        print("All members have completed their dailies today!")
        return

    print(f"Members who have NOT completed their dailies ({len(inactive_members)} found):")
    print("-" * 50)
    for member in inactive_members:
        name = member.get(name_column, "Unknown")
        fan_gain = member.get("Daily Fan Gain", "N/A")
        print(f"  {name} (Daily Fan Gain: {fan_gain})")


def main(filepath: str = "sample_club_data.csv") -> None:
    try:
        rows = load_csv(filepath)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.", file=sys.stderr)
        sys.exit(1)

    inactive = filter_inactive_members(rows)
    print_report(inactive)


if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "sample_club_data.csv"
    main(csv_file)
