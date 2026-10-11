#!/usr/bin/env python3
"""Privacy-first contact-list audit; standard library only, no external API calls."""
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

FIELDS = ("name", "phone", "email")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalize_header(value):
    return re.sub(r"[^a-z0-9]+", "_", (value or "").strip().casefold()).strip("_")


def excel_safe(value, force_text=False):
    """Protect exported text against CSV formula execution or number coercion."""
    value = value or ""
    if value and (force_text or value[0] in "=+@-\t\r\n"):
        return "'" + value
    return value


def audit(source, cleaned, exceptions):
    source, cleaned, exceptions = map(Path, (source, cleaned, exceptions))
    paths = [p.resolve() for p in (source, cleaned, exceptions)]
    if len(set(paths)) != len(paths):
        raise ValueError("Input and output paths must all differ")
    with source.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError("Missing CSV header")
        headers = [normalize_header(v) for v in reader.fieldnames]
        if len(set(headers)) != len(headers) or any(not v for v in headers):
            raise ValueError("Invalid or duplicate column headings")
        required = set(FIELDS)
        if not required.issubset(set(headers)):
            raise ValueError("Required columns: name, phone, email")
        seen, outrows, issue_rows = {}, [], []
        for line, rec in enumerate(reader, 2):
            problems = []
            if None in rec:
                problems.append("extra_columns")
            row = {
                h: re.sub(r"\s+", " ", (rec.get(original) or "")).strip()
                for h, original in zip(headers, reader.fieldnames)
            }
            email = row["email"].casefold()
            phone = row["phone"]
            if not row["name"]:
                problems.append("missing_name")
            if not phone:
                problems.append("missing_phone")
            if not email:
                problems.append("missing_email")
            elif not EMAIL_RE.fullmatch(email):
                problems.append("email_format_review")
            if email and email in seen:
                problems.append("possible_duplicate_email_of_row_" + str(seen[email]))
            elif email:
                seen[email] = line
            flagged = "REVIEW" if problems else "PASS"
            outrows.append((line, row, flagged, problems))
            if problems:
                issue_rows.append([str(line), row["name"], row["email"], "; ".join(problems)])
    for path in (cleaned, exceptions):
        path.parent.mkdir(parents=True, exist_ok=True)
    with cleaned.open("w", encoding="utf-8-sig", newline="") as stream:
        fieldnames = ["source_row", *headers, "qa_status", "review_notes"]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for line, row, flagged, problems in outrows:
            safe = {k: excel_safe(v, force_text=(k == "phone"))
                    for k, v in row.items()}
            writer.writerow({
                "source_row": line, **safe, "qa_status": flagged,
                "review_notes": "; ".join(problems)
            })
    with exceptions.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["source_row", "name", "email", "issues"])
        for line, name, email, problems in issue_rows:
            writer.writerow([
                line, excel_safe(name), excel_safe(email), excel_safe(problems)
            ])
    return {
        "input_records": len(outrows),
        "pass_records": sum(flagged == "PASS" for _, _, flagged, _ in outrows),
        "review_records": len(issue_rows),
        "issues": dict(Counter(p for _, _, _, ps in outrows for p in ps)),
        "data_policy": "Synthetic demo only; review flags do not delete source records."
    }


def main():
    parser = argparse.ArgumentParser(description="Audit contact CSV; retain all records")
    parser.add_argument("source")
    parser.add_argument("cleaned")
    parser.add_argument("exceptions")
    args = parser.parse_args()
    print(json.dumps(audit(args.source, args.cleaned, args.exceptions), indent=2))


if __name__ == "__main__":
    main()
