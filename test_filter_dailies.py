"""Tests for filter_dailies.py"""

import io
import unittest
from unittest.mock import patch, mock_open

from filter_dailies import filter_inactive_members, print_report, load_csv, DAILY_FAN_THRESHOLD


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


if __name__ == "__main__":
    unittest.main()
