import csv
import tempfile
import unittest
from pathlib import Path

from contact_quality import audit, excel_safe


class ContactQualityTests(unittest.TestCase):
    def test_preserves_records_and_flags_duplicates(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            source = base / "input.csv"
            source.write_text(
                "name,phone,email\n"
                "Ayu,081234567890,ayu@example.test\n"
                "Bima,+628123456789,bima@example.test\n"
                "Ayu Duplicate,081234567890,AYU@example.test\n"
                "Cita,,bad-at-example.test\n",
                encoding="utf-8"
            )
            result = audit(source, base / "cleaned.csv", base / "issues.csv")
            self.assertEqual(result["input_records"], 4)
            self.assertEqual(result["pass_records"], 2)
            self.assertEqual(result["review_records"], 2)
            with (base / "cleaned.csv").open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 4)
            self.assertEqual(rows[0]["phone"], "'081234567890")
            self.assertEqual(rows[1]["phone"], "'+628123456789")
            self.assertIn("duplicate", rows[2]["review_notes"])
            self.assertIn("missing_phone", rows[3]["review_notes"])
            self.assertIn("email_format_review", rows[3]["review_notes"])

    def test_blocks_formula_interpretation(self):
        self.assertEqual(excel_safe("=SUM(1,2)"), "'=SUM(1,2)")
        self.assertEqual(excel_safe("+44"), "'+44")
        self.assertEqual(excel_safe("plain"), "plain")

    def test_refuses_overwriting_input(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "one.csv"
            source.write_text("name,phone,email\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                audit(source, source, Path(d) / "exceptions.csv")

    def test_refuses_duplicate_headers(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "input.csv"
            source.write_text("Name,name,phone,email\nA,A,01,a@example.test\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                audit(source, Path(d) / "out.csv", Path(d) / "issues.csv")


if __name__ == "__main__":
    unittest.main()
