"""Regression tests for qualitative neonatal jaundice documentation."""
import csv
import json
from pathlib import Path

import pytest

from kramer import ZONES, calculate_score, assess_row, process_csv, main


def test_zones_are_descriptive():
    assert len(ZONES) == 6
    for zone in range(6):
        result = calculate_score({"zone": zone})
        assert result["zone"] == zone
        assert result["distribution"] == ZONES[zone]
        assert "score" not in result
        assert "tier" not in result
        assert "bilirubin" in result["limitation"].lower()


def test_early_jaundice_requires_urgent_serum_measurement():
    result = calculate_score({"zone": "1", "age_hours": "12", "gestational_weeks": "39"})
    assert result["early_jaundice"] is True
    assert "urgent serum bilirubin" in result["action"].lower()


def test_no_early_alert_at_24_hours():
    assert calculate_score({"zone": 2, "age_hours": 24})["early_jaundice"] is False


def test_premature_infant_context():
    result = calculate_score({"zone": 3, "gestational_weeks": 33})
    assert "prematurity-specific" in result["action"]
    assert "serum bilirubin" in result["action"]


def test_absent_jaundice_does_not_rule_out_hyperbilirubinemia():
    result = calculate_score({"zone": 0})
    assert "does not exclude" in result["action"]


@pytest.mark.parametrize("bad", [-1, 6, 1.5, "2.0", "", None, True, "high"])
def test_invalid_zones(bad):
    with pytest.raises(ValueError):
        calculate_score({"zone": bad})


@pytest.mark.parametrize("field,value", [
    ("age_hours", -1),
    ("age_hours", 673),
    ("age_hours", float("nan")),
    ("gestational_weeks", 21),
    ("gestational_weeks", float("inf")),
    ("gestational_weeks", "invalid"),
])
def test_invalid_measurements(field, value):
    with pytest.raises(ValueError):
        calculate_score({"zone": 1, field: value})


def test_wrong_input_types():
    with pytest.raises(TypeError):
        calculate_score([])
    with pytest.raises(TypeError):
        assess_row("row")


def test_csv_processing(tmp_path):
    inp, out = tmp_path / "input.csv", tmp_path / "output.csv"
    inp.write_text(
        "record_id,zone,age_hours,gestational_weeks\n"
        "EX-1,1,12,40\nEX-2,4,60,36\n", encoding="utf-8"
    )
    results = process_csv(inp, out)
    assert len(results) == 2
    assert results[0]["early_jaundice"]
    with out.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert rows[1]["distribution"] == ZONES[4]
    assert rows[0]["record_id"] == "EX-1"


def test_batch_validation_is_atomic(tmp_path):
    inp, out = tmp_path / "in.csv", tmp_path / "out.csv"
    inp.write_text("zone\n1\n99\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Line 3"):
        process_csv(inp, out)
    assert not out.exists()


def test_csv_input_and_output_cannot_match(tmp_path):
    path = tmp_path / "same.csv"
    path.write_text("zone\n2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        process_csv(path, path)


def test_csv_duplicate_header(tmp_path):
    inp, out = tmp_path / "in.csv", tmp_path / "out.csv"
    inp.write_text("zone,ZONE\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        process_csv(inp, out)


def test_single_cli(capsys):
    assert main(["single", "--zone", "2", "--age-hours", "30"]) == 0
    assert json.loads(capsys.readouterr().out)["zone"] == 2


def test_batch_cli(tmp_path, capsys):
    inp, out = tmp_path / "in.csv", tmp_path / "out.csv"
    inp.write_text("zone\n3\n", encoding="utf-8")
    assert main(["batch", "--input", str(inp), "--output", str(out)]) == 0
    assert out.exists()
