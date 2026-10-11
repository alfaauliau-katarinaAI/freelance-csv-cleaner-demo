# KATARINA Freelance — Data Cleaning & Contact QA Portfolio

**Public, synthetic, AI-assisted software demo.** This repository is **not** a completed paid-client project, an endorsement, or a guarantee of zero errors on external client files. No real customer information is stored here.

## 1) CSV Cleaner

`clean_csv.py` offers:

- Normalized headings and whitespace; comma, semicolon, and tab CSV input.
- Case-insensitive duplicate removal by a configurable key, recorded in the audit.
- Missing required-value review and malformed-row counts.
- Protection against spreadsheet formula injection in CSV outputs.
- JSON audit record. Python standard library only.

Example:

```bash
python clean_csv.py examples/sample.csv examples/cleaned.csv --key Email --required Email
```

## 2) Customer Contact Quality Audit

`contact_quality.py` is designed for data-entry briefs that require careful review of names, emails and telephone numbers:

- **Preserves every input contact** rather than silently removing suspected duplicates.
- Flags case-insensitive duplicate emails, missing fields, invalid email formatting and unexpected columns.
- Preserves phone number leading zeros and plus-prefixed country codes as Excel-safe CSV text.
- Produces two deliverables: cleaned/reviewed CSV and separate exceptions CSV.
- Does not transmit data to an AI API, web service, or any external endpoint.

Try this fully fictional fixture:

```bash
python contact_quality.py examples/synthetic_contacts.csv examples/reviewed_contacts.csv examples/exceptions.csv
python -m unittest discover -s tests -v
```

**Verification (11 October 2026):** 8 Python unit tests passed on the authorized KATARINA development VPS, including four tests covering contact QA. Re-run tests on the client-specific input sample and document all exceptions before delivery.

## Client delivery approach

1. Agree on source file format, record count, duplicate handling, deliverable format (CSV vs .xlsx), schedule, payment milestone, confidentiality, and authorized processing environment.
2. Process data only under client instructions. Never upload personal contacts to public repositories or third-party AI services without specific authorization.
3. Return the cleaned table plus a review/exceptions report and reconcile output records against source records.
4. Flag ambiguity for client decisions instead of inventing missing values.

The sample workbook used in sales demonstrations is built from fictional records; direct spreadsheet export is prepared per client requirements.

**Disclosure:** Developed with AI assistance and locally tested. No client revenue, contracts or project outcomes are claimed here.
