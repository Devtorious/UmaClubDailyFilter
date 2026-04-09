import csv
import re
import sys
from typing import Optional

DAILY_FAN_THRESHOLD = 300
NULL_MARKER = "-"
DEFAULT_FILE = "sample_club_data.csv"


def load_csv(filepath: str) -> list[dict]:
    """Return all rows from *filepath* as a list of dicts."""
    with open(filepath, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


# ---------------------------------------------------------------------------
# Legacy-format helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Monthly-format helpers
# ---------------------------------------------------------------------------

def _is_monthly_format(rows: list[dict]) -> bool:
    """Return True when the CSV uses cumulative per-day columns (e.g. "Day 1")."""
    if not rows:
        return False
    return any(re.match(r"Day \d+$", h.strip()) for h in rows[0].keys())


def _get_day_columns(rows: list[dict]) -> list[str]:
    """Return day column names sorted numerically (e.g. Day 1, Day 2, …)."""
    if not rows:
        return []
    day_cols = [h for h in rows[0].keys() if re.match(r"Day \d+$", h.strip())]
    day_cols.sort(key=lambda x: int(x.split()[-1]))
    return day_cols


def analyze_monthly_data(rows: list[dict]) -> list[dict]:
    """Analyze monthly cumulative fan data and return members who missed dailies.

    For each trainer the function computes the per-day gain from consecutive
    non-empty day values.  A day is counted as *missed* when the gain is
    strictly below DAILY_FAN_THRESHOLD.  A gap (empty day) resets the running
    baseline so that cross-gap comparisons are never made.

    Returns a list of dicts (one per trainer who missed at least one day) with
    the keys: "Trainer", "missed_days", "total_days".
    """
    day_cols = _get_day_columns(rows)
    results = []

    for row in rows:
        trainer = row.get("Trainer", "Unknown").strip()

        # Build a mapping of column → integer value for non-empty days.
        day_values: dict[str, int] = {}
        for col in day_cols:
            raw = row.get(col, "").strip()
            if raw == NULL_MARKER or raw == "":
                continue
            try:
                day_values[col] = int(raw)
            except ValueError:
                continue

        missed = 0
        total_checked = 0
        prev_val: Optional[int] = None

        for col in day_cols:
            if col not in day_values:
                # Gap in data: reset the baseline so we never compare across it.
                prev_val = None
                continue
            curr_val = day_values[col]
            if prev_val is not None:
                gain = curr_val - prev_val
                total_checked += 1
                if gain < DAILY_FAN_THRESHOLD:
                    missed += 1
            prev_val = curr_val

        if missed > 0:
            results.append(
                {
                    "Trainer": trainer,
                    "missed_days": missed,
                    "total_days": total_checked,
                }
            )

    return results


def print_monthly_report(results: list[dict]) -> None:
    """Print a report of members who missed dailies in the monthly data."""
    if not results:
        print("All members have completed their dailies this month!")
        return

    print(
        f"Members who have NOT completed their dailies this month"
        f" ({len(results)} found):"
    )
    print("-" * 50)
    for member in results:
        trainer = member["Trainer"]
        missed = member["missed_days"]
        total = member["total_days"]
        print(
            f"  Trainer {trainer}: missed {missed} out of {total} checked day(s)"
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(filepath: Optional[str] = None) -> None:
    if filepath is None:
        user_input = input(f"Enter CSV filename (default: {DEFAULT_FILE}): ").strip()
        filepath = user_input if user_input else DEFAULT_FILE

    try:
        rows = load_csv(filepath)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.", file=sys.stderr)
        sys.exit(1)

    if _is_monthly_format(rows):
        results = analyze_monthly_data(rows)
        print_monthly_report(results)
    else:
        inactive = filter_inactive_members(rows)
        print_report(inactive)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
