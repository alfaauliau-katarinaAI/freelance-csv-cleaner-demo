#!/usr/bin/env python3
"""Auditable CSV cleaning for Excel-compatible deliverables (stdlib only)."""
import argparse
import csv
import json
import re
from pathlib import Path
from collections import Counter


def normalized_header(label):
    return re.sub(r"[^a-z0-9]+", "_", label.strip().casefold()).strip("_") or "column"


def unique_headers(headers):
    counters = Counter()
    result = []
    for header in headers:
        cleaned = normalized_header(header)
        counters[cleaned] += 1
        result.append(cleaned if counters[cleaned] == 1 else cleaned + "_" + str(counters[cleaned]))
    return result


def safe_cell(value):
    cleaned = re.sub(r"\s+", " ", value).strip()
    dangerous = bool(cleaned) and (
        cleaned[0] in "=+@" or
        (cleaned[0] == "-" and not re.fullmatch(r"-\d+(?:\.\d+)?", cleaned))
    )
    return ("'" + cleaned if dangerous else cleaned), dangerous


def clean_csv(source, output, key="", required=()):
    source, output = Path(source), Path(output)
    if source.resolve() == output.resolve():
        raise ValueError("Input and output must differ; original data will not be overwritten.")
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(handle, dialect)
        try:
            headers = unique_headers(next(reader))
        except StopIteration as exc:
            raise ValueError("Input is empty") from exc
        key = normalized_header(key) if key else ""
        required = [normalized_header(r) for r in required]
        unknown = [name for name in [key, *required] if name and name not in headers]
        if unknown:
            raise ValueError("Unknown columns: " + ", ".join(unknown) + "; available: " + ", ".join(headers))
        seen, cleaned_rows = set(), []
        duplicates = malformed = escaped = 0
        missing = Counter()
        for row in reader:
            if not row or all(not part.strip() for part in row):
                continue
            if len(row) != len(headers):
                malformed += 1
                continue
            values = []
            for cell in row:
                value, is_escaped = safe_cell(cell)
                escaped += int(is_escaped)
                values.append(value)
            record = dict(zip(headers, values))
            if key and record[key]:
                norm = record[key].casefold()
                if norm in seen:
                    duplicates += 1
                    continue
                seen.add(norm)
            for name in required:
                if not record[name]:
                    missing[name] += 1
            cleaned_rows.append(record)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(cleaned_rows)
    audit = {
        "source_file": source.name, "output_file": output.name,
        "headers": headers, "rows_written": len(cleaned_rows),
        "duplicate_keys_removed": duplicates, "malformed_rows_skipped": malformed,
        "formula_like_cells_escaped": escaped, "missing_required_by_column": dict(missing),
        "review_note": "Incomplete rows are preserved and flagged, not silently deleted."
    }
    output.with_suffix(".audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return audit


def main():
    parser = argparse.ArgumentParser(description="Safe CSV cleaner and audit report")
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--key", default="")
    parser.add_argument("--required", action="append", default=[])
    args = parser.parse_args()
    print(json.dumps(clean_csv(args.input, args.output, args.key, args.required), indent=2))


if __name__ == "__main__":
    main()
