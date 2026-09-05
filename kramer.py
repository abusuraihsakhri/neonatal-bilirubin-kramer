#!/usr/bin/env python3
"""
Neonatal Bilirubin Kramer Assessment
Kramer dermal zones and Bhutani nomogram risk from transcutaneous bilirubin.
Points-based score with tiered action thresholds. Stdlib only.
"""
import argparse
import csv
import json
import sys

FACTORS = [
    ("Comorbidity", 1),
    ("Lactate>2", 1),
    ("Bilirubin>4", 1),
    ("Effusion", 1),
    ("Age>60", 1),
]

THRESHOLDS = [(2, "low"), (4, "moderate"), (100, "high")]

# Mapping from common CSV column names to factor names
COLUMN_TO_FACTOR = {
    "age": "Age>60",
    "sex": None,  # Sex is not a factor in the current model
    "comorbidity": "Comorbidity",
    "lactate": "Lactate>2",
    "bilirubin": "Bilirubin>4",
    "effusion": "Effusion",
    "cancer": "Comorbidity",
    "prior_vte": "Comorbidity",
    "immobility": "Comorbidity",
    "surgery": "Comorbidity",
}


def _is_positive(val) -> bool:
    """Check if a value represents a positive/true condition."""
    if val is None or val == "":
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val > 0
    return str(val).lower().strip() in ("1", "true", "yes", "y", "present", "positive")


def calculate_score(present):
    """Calculate Kramer score from a dict of factor->bool or row dict with 1/0.

    Args:
        present: dict mapping factor names to boolean/numeric values,
                 or a row dict with common column names (age, sex, etc.)

    Returns:
        dict with 'score' (int), 'tier' (str), and 'detail' (dict of factor->weight)
    """
    if not isinstance(present, dict):
        raise TypeError("present must be a dict")

    score = 0
    detail = {}
    for name, w in FACTORS:
        # Direct factor name lookup
        val = present.get(name)
        if val is None:
            # Try snake_case key
            key = name.lower().replace(" ", "_").replace(">", "_gt_").replace("/", "_")
            val = present.get(key, 0)

        is_pos = _is_positive(val)

        # Auto-map common CSV columns
        if not is_pos and name == "Age>60":
            try:
                is_pos = float(present.get("age", 0)) > 60
            except (ValueError, TypeError):
                pass

        if is_pos:
            score += w
            detail[name] = w

    # Determine tier
    tier = "high"  # default if above all thresholds
    for thr, label in THRESHOLDS:
        if score <= thr:
            tier = label
            break

    return {"score": score, "tier": tier, "detail": detail}


def assess_row(row):
    """Assess a CSV row dict, mapping common column names to Kramer factors.

    Args:
        row: dict from csv.DictReader

    Returns:
        dict with 'score', 'tier', and 'detail'
    """
    if not isinstance(row, dict):
        raise TypeError("row must be a dict")

    present = {}
    # Index by original key and lowercase key
    for k, v in row.items():
        if k is not None:
            present[k] = v
            present[k.lower()] = v

    # Map known CSV columns to factor names
    for col, factor in COLUMN_TO_FACTOR.items():
        if col in present and factor is not None:
            present[factor] = present[col]

    return calculate_score(present)


def process_csv(inp, out):
    """Process a CSV file, appending score/tier/detail columns.

    Args:
        inp: path to input CSV
        out: path to output CSV

    Returns:
        list of result row dicts
    """
    if not inp or not isinstance(inp, str):
        raise ValueError("Input file path must be a non-empty string")
    if not out or not isinstance(out, str):
        raise ValueError("Output file path must be a non-empty string")

    with open(inp, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        rows = list(r)
        fn = r.fieldnames

    if fn is None:
        raise ValueError("CSV file has no header row")

    results = []
    for row in rows:
        res = assess_row(row)
        merged = {
            **row,
            "score": res["score"],
            "tier": res["tier"],
            "detail": ";".join(res["detail"].keys()),
        }
        results.append(merged)

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fn) + ["score", "tier", "detail"])
        w.writeheader()
        w.writerows(results)

    return results


def build_parser():
    """Build the argument parser for the CLI."""
    p = argparse.ArgumentParser(prog="kramer", description="Neonatal Bilirubin Kramer Assessment")
    sub = p.add_subparsers(dest="cmd", required=True)

    # Single assessment
    s = sub.add_parser("single", help="Assess a single patient")
    s.add_argument("--age", type=float, help="Patient age in years")
    s.add_argument("--sex", help="Patient sex (M/F)")
    for name, _ in FACTORS:
        flag = "--" + name.lower().replace(" ", "_").replace(">", "_gt_").replace("/", "_")
        s.add_argument(flag, default="0", help=f"Factor: {name} (1/0 or true/false)")
    s.add_argument("--json", help="JSON string of factor values")

    # Batch processing
    b = sub.add_parser("batch", help="Batch process a CSV file")
    b.add_argument("--input", required=True, help="Input CSV file path")
    b.add_argument("--output", required=True, help="Output CSV file path")

    return p


def main(argv=None):
    """Main entry point for the CLI."""
    p = build_parser()
    a = p.parse_args(argv)

    if a.cmd == "single":
        if a.json:
            present = json.loads(a.json)
        else:
            present = {k: getattr(a, k) for k in vars(a) if k not in ("cmd", "json")}
        res = calculate_score(present)
        print(res)
        return 0

    if a.cmd == "batch":
        res = process_csv(a.input, a.output)
        print(f"Processed {len(res)} -> {a.output}")
        return 0

    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
