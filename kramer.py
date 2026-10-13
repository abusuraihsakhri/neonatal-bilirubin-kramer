#!/usr/bin/env python3
"""Qualitative Kramer-zone documentation for neonatal jaundice.

Kramer zones describe cephalocaudal distribution of visible jaundice.
They do NOT estimate bilirubin concentration, phototherapy eligibility,
neurotoxicity risk, or a Bhutani/AAP risk tier.
"""
import argparse
import csv
import json
import math
from pathlib import Path

ZONES = {
    0: "No visible jaundice reported",
    1: "Head and neck",
    2: "Upper trunk (chest and upper abdomen)",
    3: "Lower abdomen and thighs",
    4: "Arms and lower legs",
    5: "Palms and soles",
}
OUTPUT_FIELDS = ("zone", "distribution", "early_jaundice", "action", "limitation")


def _number(value, name, minimum, maximum):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return result


def calculate_score(present):
    """Describe visual distribution; do not calculate a clinical risk score.

    Required: zone (integer 0-5).
    Optional: age_hours (0-672), gestational_weeks (22-44).

    Returns a descriptive record, never a bilirubin estimate or risk tier.
    """
    if not isinstance(present, dict):
        raise TypeError("present must be a dict")
    raw_zone = present.get("zone")
    if isinstance(raw_zone, bool) or raw_zone is None or str(raw_zone).strip() not in {
        "0", "1", "2", "3", "4", "5"
    }:
        raise ValueError("zone must be an integer between 0 and 5")
    zone = int(raw_zone)
    age_hours = _number(present.get("age_hours"), "age_hours", 0, 672)
    gestational_weeks = _number(
        present.get("gestational_weeks"), "gestational_weeks", 22, 44
    )

    early = zone > 0 and age_hours is not None and age_hours < 24
    if early:
        action = (
            "Visible jaundice before 24 hours: urgent serum bilirubin "
            "measurement and clinical assessment are required."
        )
    elif zone > 0:
        action = (
            "Visible jaundice: obtain objective bilirubin measurement "
            "and assess using an age- and gestation-appropriate guideline."
        )
    else:
        action = (
            "No visible jaundice recorded. This does not exclude "
            "hyperbilirubinemia; follow routine objective bilirubin screening."
        )

    if gestational_weeks is not None and gestational_weeks < 35:
        action += (
            " Gestation under 35 weeks: use serum bilirubin and a "
            "prematurity-specific clinical protocol."
        )

    return {
        "zone": zone,
        "distribution": ZONES[zone],
        "age_hours": age_hours,
        "gestational_weeks": gestational_weeks,
        "early_jaundice": early,
        "action": action,
        "limitation": (
            "Kramer distribution is observational only. It cannot determine "
            "bilirubin concentration, risk category, or treatment threshold."
        ),
    }


def assess_row(row):
    """Evaluate a de-identified CSV row with a required 'zone' column."""
    if not isinstance(row, dict):
        raise TypeError("row must be a dict")
    normalized = {
        str(key).strip().lower(): value.strip() if isinstance(value, str) else value
        for key, value in row.items() if key is not None
    }
    return calculate_score(normalized)


def process_csv(inp, out):
    """Append descriptive zone fields to a de-identified CSV.

    Reject duplicate headers or pre-existing computed fields to avoid
    ambiguous data, and avoid partially writing output on validation error.
    """
    if not isinstance(inp, (str, Path)) or not str(inp):
        raise ValueError("Input file path must be provided")
    if not isinstance(out, (str, Path)) or not str(out):
        raise ValueError("Output file path must be provided")
    if Path(inp).resolve() == Path(out).resolve():
        raise ValueError("Input and output paths must differ")

    with open(inp, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        if not headers or "zone" not in [h.strip().lower() for h in headers]:
            raise ValueError("CSV header must include 'zone'")
        normalized_headers = [h.strip().lower() for h in headers]
        if len(set(normalized_headers)) != len(headers):
            raise ValueError("CSV contains duplicate column names")
        if any(h in OUTPUT_FIELDS and h != "zone" for h in normalized_headers):
            raise ValueError("CSV already contains output columns")
        results = []
        for line_no, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"Unexpected extra CSV values on line {line_no}")
            try:
                assessed = assess_row(row)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Line {line_no}: {exc}") from exc
            results.append({
                **row,
                "zone": assessed["zone"],
                "distribution": assessed["distribution"],
                "early_jaundice": assessed["early_jaundice"],
                "action": assessed["action"],
                "limitation": assessed["limitation"],
            })

    output_headers = list(headers)
    output_headers.extend(h for h in OUTPUT_FIELDS if h not in normalized_headers)
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_headers)
        writer.writeheader()
        writer.writerows(results)
    return results


def build_parser():
    parser = argparse.ArgumentParser(
        prog="kramer", description="Observational neonatal Kramer-zone documentation"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    single = sub.add_parser("single", help="Document one visual assessment")
    single.add_argument("--zone", type=int, choices=range(6))
    single.add_argument("--age-hours", type=float)
    single.add_argument("--gestational-weeks", type=float)
    single.add_argument("--json", help="JSON object with zone and optional context")
    batch = sub.add_parser("batch", help="Assess a de-identified CSV file")
    batch.add_argument("--input", required=True)
    batch.add_argument("--output", required=True)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.cmd == "single":
        if args.json is not None:
            data = json.loads(args.json)
        else:
            if args.zone is None:
                raise ValueError("single requires --zone or --json with zone")
            data = {
                "zone": args.zone,
                "age_hours": args.age_hours,
                "gestational_weeks": args.gestational_weeks,
            }
        print(json.dumps(calculate_score(data), indent=2))
        return 0
    if args.cmd == "batch":
        results = process_csv(args.input, args.output)
        print(f"Processed {len(results)} records -> {args.output}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
