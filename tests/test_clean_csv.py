import csv
import tempfile
import unittest
from pathlib import Path
from clean_csv import clean_csv, safe_cell, unique_headers


class CsvCleanerTests(unittest.TestCase):
    def test_dedup_and_audit(self):
        with tempfile.TemporaryDirectory() as d:
            source, out = Path(d) / "input.csv", Path(d) / "output.csv"
            source.write_text(' Name , Email ,Value\n Ana ,a@example.com,-4\nAna,A@example.com,7\nBudi,,=1+1\n', encoding="utf-8")
            report = clean_csv(source, out, key="email", required=["email"])
            self.assertEqual(report["rows_written"], 2)
            self.assertEqual(report["duplicate_keys_removed"], 1)
            self.assertEqual(report["missing_required_by_column"], {"email": 1})
            self.assertEqual(report["formula_like_cells_escaped"], 1)
            with out.open("r", newline="", encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(rows[0]["value"], "-4")
            self.assertTrue(rows[1]["value"].startswith("'="))
            self.assertTrue(out.with_suffix(".audit.json").exists())

    def test_safe_cells(self):
        self.assertEqual(safe_cell("=SUM(A1)"), ("'=SUM(A1)", True))
        self.assertEqual(safe_cell("-100.5"), ("-100.5", False))
        self.assertEqual(safe_cell("hello"), ("hello", False))

    def test_unique_columns(self):
        self.assertEqual(unique_headers(["Name", " NAME ", "name"]), ["name", "name_2", "name_3"])

    def test_unknown_key(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "input.csv", Path(d) / "out.csv"
            a.write_text("Name\nA\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                clean_csv(a, b, key="email")
            self.assertFalse(b.exists())


if __name__ == "__main__":
    unittest.main()
