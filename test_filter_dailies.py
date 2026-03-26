"""Tests for filter_dailies.py"""

import io
import unittest
from unittest.mock import patch, mock_open

from filter_dailies import (
    filter_inactive_members,
    print_report,
    load_csv,
    DAILY_FAN_THRESHOLD,
    _is_monthly_format,
    _get_day_columns,
    analyze_monthly_data,
    print_monthly_report,
)


SAMPLE_ROWS = [
    {"Name": "TrainerAkira", "Daily Fan Gain": "1500", "Rank": "S1"},
    {"Name": "TrainerHana",  "Daily Fan Gain": "250",  "Rank": "A2"},
    {"Name": "TrainerSora",  "Daily Fan Gain": "-",    "Rank": "B3"},
    {"Name": "TrainerRiku",  "Daily Fan Gain": "0",    "Rank": "C1"},
    {"Name": "TrainerMio",   "Daily Fan Gain": "300",  "Rank": "A1"},
    {"Name": "TrainerKai",   "Daily Fan Gain": "150",  "Rank": "B2"},
    {"Name": "TrainerYuki",  "Daily Fan Gain": "-",    "Rank": "C2"},
    {"Name": "TrainerNana",  "Daily Fan Gain": "2400", "Rank": "S3"},
    {"Name": "TrainerTomo",  "Daily Fan Gain": "299",  "Rank": "A3"},
    {"Name": "TrainerZen",   "Daily Fan Gain": "600",  "Rank": "A2"},
]


class TestFilterInactiveMembers(unittest.TestCase):
    def test_returns_members_below_threshold(self):
        inactive = filter_inactive_members(SAMPLE_ROWS)
        names = [r["Name"] for r in inactive]
        self.assertIn("TrainerHana", names)   # 250 < 300
        self.assertIn("TrainerRiku", names)   # 0 < 300
        self.assertIn("TrainerKai", names)    # 150 < 300
        self.assertIn("TrainerTomo", names)   # 299 < 300

    def test_excludes_members_at_or_above_threshold(self):
        inactive = filter_inactive_members(SAMPLE_ROWS)
        names = [r["Name"] for r in inactive]
        self.assertNotIn("TrainerAkira", names)  # 1500 >= 300
        self.assertNotIn("TrainerMio", names)    # 300 == threshold, not strictly less
        self.assertNotIn("TrainerNana", names)   # 2400 >= 300
        self.assertNotIn("TrainerZen", names)    # 600 >= 300

    def test_dash_values_are_ignored(self):
        inactive = filter_inactive_members(SAMPLE_ROWS)
        names = [r["Name"] for r in inactive]
        self.assertNotIn("TrainerSora", names)   # "-" → null, ignored
        self.assertNotIn("TrainerYuki", names)   # "-" → null, ignored

    def test_empty_value_is_ignored(self):
        rows = [{"Name": "TrainerX", "Daily Fan Gain": ""}]
        self.assertEqual(filter_inactive_members(rows), [])

    def test_non_numeric_value_is_ignored(self):
        rows = [{"Name": "TrainerX", "Daily Fan Gain": "N/A"}]
        self.assertEqual(filter_inactive_members(rows), [])

    def test_exact_threshold_not_inactive(self):
        rows = [{"Name": "TrainerBorder", "Daily Fan Gain": str(DAILY_FAN_THRESHOLD)}]
        self.assertEqual(filter_inactive_members(rows), [])

    def test_one_below_threshold(self):
        rows = [{"Name": "TrainerBorder", "Daily Fan Gain": str(DAILY_FAN_THRESHOLD - 1)}]
        self.assertEqual(len(filter_inactive_members(rows)), 1)

    def test_empty_input(self):
        self.assertEqual(filter_inactive_members([]), [])

    def test_all_null_values(self):
        rows = [
            {"Name": "A", "Daily Fan Gain": "-"},
            {"Name": "B", "Daily Fan Gain": "-"},
        ]
        self.assertEqual(filter_inactive_members(rows), [])

    def test_custom_column_name(self):
        rows = [{"Name": "TrainerX", "FanGain": "100"}]
        inactive = filter_inactive_members(rows, column="FanGain")
        self.assertEqual(len(inactive), 1)

    def test_missing_column_is_ignored(self):
        rows = [{"Name": "TrainerX"}]
        self.assertEqual(filter_inactive_members(rows), [])


class TestPrintReport(unittest.TestCase):
    def test_no_inactive_prints_all_done_message(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            print_report([])
            output = mock_stdout.getvalue()
        self.assertIn("All members have completed their dailies", output)

    def test_inactive_members_are_listed(self):
        inactive = [
            {"Name": "TrainerHana", "Daily Fan Gain": "250"},
            {"Name": "TrainerRiku", "Daily Fan Gain": "0"},
        ]
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            print_report(inactive)
            output = mock_stdout.getvalue()
        self.assertIn("TrainerHana", output)
        self.assertIn("TrainerRiku", output)
        self.assertIn("2 found", output)


class TestLoadCsv(unittest.TestCase):
    def test_load_csv_parses_rows(self):
        csv_content = "Name,Daily Fan Gain\nTrainerA,500\nTrainerB,100\n"
        with patch("builtins.open", mock_open(read_data=csv_content)):
            rows = load_csv("fake.csv")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Name"], "TrainerA")
        self.assertEqual(rows[1]["Daily Fan Gain"], "100")


# ---------------------------------------------------------------------------
# Monthly-format detection helpers
# ---------------------------------------------------------------------------

MONTHLY_ROWS = [
    {"Trainer": "111", "Day 1": "10000", "Day 2": "10001", "Day 3": "10500"},
    {"Trainer": "222", "Day 1": "5000",  "Day 2": "5600",  "Day 3": "6000"},
    {"Trainer": "333", "Day 1": "0",     "Day 2": "0",     "Day 3": "0"},
    {"Trainer": "444", "Day 1": "100",   "Day 2": "",       "Day 3": "800"},
]


class TestIsMonthlyFormat(unittest.TestCase):
    def test_detects_monthly_format(self):
        self.assertTrue(_is_monthly_format(MONTHLY_ROWS))

    def test_rejects_legacy_format(self):
        self.assertFalse(_is_monthly_format(SAMPLE_ROWS))

    def test_empty_rows_returns_false(self):
        self.assertFalse(_is_monthly_format([]))


class TestGetDayColumns(unittest.TestCase):
    def test_returns_day_columns_sorted(self):
        rows = [{"Trainer": "1", "Day 3": "0", "Day 1": "0", "Day 10": "0", "Day 2": "0"}]
        cols = _get_day_columns(rows)
        self.assertEqual(cols, ["Day 1", "Day 2", "Day 3", "Day 10"])

    def test_excludes_non_day_columns(self):
        cols = _get_day_columns(MONTHLY_ROWS)
        self.assertNotIn("Trainer", cols)
        self.assertIn("Day 1", cols)
        self.assertIn("Day 3", cols)

    def test_empty_rows_returns_empty(self):
        self.assertEqual(_get_day_columns([]), [])


class TestAnalyzeMonthlyData(unittest.TestCase):
    def test_detects_missed_days(self):
        # Trainer 111: Day2-Day1=1 (missed), Day3-Day2=499 (ok) → 1 missed
        results = analyze_monthly_data(MONTHLY_ROWS)
        trainer_map = {r["Trainer"]: r for r in results}
        self.assertIn("111", trainer_map)
        self.assertEqual(trainer_map["111"]["missed_days"], 1)
        self.assertEqual(trainer_map["111"]["total_days"], 2)

    def test_all_ok_not_returned(self):
        # Trainer 222: Day2-Day1=600 (ok), Day3-Day2=400 (ok)
        results = analyze_monthly_data(MONTHLY_ROWS)
        trainer_map = {r["Trainer"]: r for r in results}
        self.assertNotIn("222", trainer_map)

    def test_all_zeros_all_missed(self):
        # Trainer 333: all gains are 0 < 300
        results = analyze_monthly_data(MONTHLY_ROWS)
        trainer_map = {r["Trainer"]: r for r in results}
        self.assertIn("333", trainer_map)
        self.assertEqual(trainer_map["333"]["missed_days"], 2)

    def test_gap_resets_baseline(self):
        # Trainer 444: Day 2 is empty → Day3 not compared to Day1;
        # Day2-Day1 not computable (Day2 empty), Day3 has no prior → 0 comparisons
        results = analyze_monthly_data(MONTHLY_ROWS)
        trainer_map = {r["Trainer"]: r for r in results}
        self.assertNotIn("444", trainer_map)

    def test_empty_rows_returns_empty(self):
        self.assertEqual(analyze_monthly_data([]), [])

    def test_no_day_columns_returns_empty(self):
        rows = [{"Trainer": "999"}]
        self.assertEqual(analyze_monthly_data(rows), [])

    def test_single_day_no_comparison(self):
        rows = [{"Trainer": "X", "Day 1": "0"}]
        self.assertEqual(analyze_monthly_data(rows), [])

    def test_dash_values_treated_as_gap(self):
        rows = [{"Trainer": "Y", "Day 1": "1000", "Day 2": "-", "Day 3": "1001"}]
        # Day 2 is a gap; Day 3 is not compared to Day 1 → no missed days counted
        self.assertEqual(analyze_monthly_data(rows), [])

    def test_exact_threshold_not_missed(self):
        rows = [{"Trainer": "Z", "Day 1": "0", "Day 2": str(DAILY_FAN_THRESHOLD)}]
        self.assertEqual(analyze_monthly_data(rows), [])

    def test_one_below_threshold_is_missed(self):
        rows = [{"Trainer": "Z", "Day 1": "0", "Day 2": str(DAILY_FAN_THRESHOLD - 1)}]
        results = analyze_monthly_data(rows)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["missed_days"], 1)


class TestPrintMonthlyReport(unittest.TestCase):
    def test_no_results_prints_all_done(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            print_monthly_report([])
            output = mock_stdout.getvalue()
        self.assertIn("All members have completed their dailies this month", output)

    def test_results_are_listed(self):
        results = [
            {"Trainer": "111222", "missed_days": 3, "total_days": 10},
            {"Trainer": "333444", "missed_days": 7, "total_days": 10},
        ]
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            print_monthly_report(results)
            output = mock_stdout.getvalue()
        self.assertIn("111222", output)
        self.assertIn("333444", output)
        self.assertIn("missed 3 out of 10", output)
        self.assertIn("2 found", output)


if __name__ == "__main__":
    unittest.main()
