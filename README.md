# Python CSV Cleaner — AI-Assisted Freelance Portfolio Sample

This is a self-contained, **synthetic code sample**, NOT a completed paid client project. It shows practical data cleaning for CSV/Excel-compatible data-entry jobs.

Features:
- Normalize headings and whitespace; handle comma, semicolon and tab-separated data.
- Case-insensitive duplicate detection by a chosen key.
- Preserve original input and incomplete rows; audit missing required values.
- Escape spreadsheet formula-like content before writing Excel-compatible CSV.
- Emit a clear JSON audit report, plus repeatable unit tests.
- Standard-library Python only: no API accounts, paid services or external dependencies.

Run using Python 3.9 or newer:

    python clean_csv.py examples/sample.csv examples/cleaned.csv --key Email --required Email
    python -m unittest discover -s tests -v

The output CSV can be opened with Excel. All names and email addresses are synthetic. Do not send customer data to an external AI service without client authorization.

**Disclosure:** The code was produced with AI assistance and locally tested. Please verify it on each client's files and requirements before delivery.
