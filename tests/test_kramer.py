"""
Comprehensive tests for the Kramer scoring engine.
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import tempfile
import csv
from kramer import (
    calculate_score,
    assess_row,
    process_csv,
    FACTORS,
    THRESHOLDS,
    _is_positive,
    COLUMN_TO_FACTOR,
)


class TestIsPositive:
    """Tests for the _is_positive helper function."""

    def test_none_is_false(self):
        assert _is_positive(None) is False

    def test_empty_string_is_false(self):
        assert _is_positive("") is False

    def test_zero_is_false(self):
        assert _is_positive(0) is False

    def test_negative_is_false(self):
        assert _is_positive(-1) is False

    def test_one_is_true(self):
        assert _is_positive(1) is True

    def test_positive_float_is_true(self):
        assert _is_positive(0.5) is True

    def test_true_bool_is_true(self):
        assert _is_positive(True) is True

    def test_false_bool_is_false(self):
        assert _is_positive(False) is False

    def test_string_one_is_true(self):
        assert _is_positive("1") is True

    def test_string_true_is_true(self):
        assert _is_positive("true") is True

    def test_string_True_is_true(self):
        assert _is_positive("True") is True

    def test_string_yes_is_true(self):
        assert _is_positive("yes") is True

    def test_string_Y_is_true(self):
        assert _is_positive("Y") is True

    def test_string_zero_is_false(self):
        assert _is_positive("0") is False

    def test_string_false_is_false(self):
        assert _is_positive("false") is False

    def test_string_no_is_false(self):
        assert _is_positive("no") is False


class TestCalculateScore:
    """Tests for the calculate_score function."""

    def test_empty_input(self):
        r = calculate_score({})
        assert r["score"] == 0
        assert r["tier"] == "low"
        assert r["detail"] == {}

    def test_age_over_60(self):
        r = calculate_score({"age": 68})
        assert r["score"] >= 1
        assert "Age>60" in r["detail"]

    def test_age_under_60(self):
        r = calculate_score({"age": 30})
        assert "Age>60" not in r["detail"]

    def test_exact_age_60(self):
        """Age exactly 60 should not trigger the Age>60 factor."""
        r = calculate_score({"age": 60})
        assert "Age>60" not in r["detail"]

    def test_age_61_triggers(self):
        r = calculate_score({"age": 61})
        assert "Age>60" in r["detail"]

    def test_all_factors_positive(self):
        present = {
            "Comorbidity": 1,
            "Lactate>2": 1,
            "Bilirubin>4": 1,
            "Effusion": 1,
            "age": 65,
        }
        r = calculate_score(present)
        assert r["score"] == 5
        assert r["tier"] == "high"

    def test_moderate_tier(self):
        """Score of 3 should be moderate tier."""
        present = {"age": 65, "Comorbidity": 1, "Bilirubin>4": 1}
        r = calculate_score(present)
        assert r["score"] == 3
        assert r["tier"] == "moderate"

    def test_low_tier(self):
        """Score of 1 should be low tier."""
        present = {"age": 65}
        r = calculate_score(present)
        assert r["score"] == 1
        assert r["tier"] == "low"

    def test_direct_factor_name(self):
        r = calculate_score({"Comorbidity": 1})
        assert "Comorbidity" in r["detail"]

    def test_snake_case_key(self):
        r = calculate_score({"lactate_gt_2": 1})
        assert "Lactate>2" in r["detail"]

    def test_invalid_input_type(self):
        with pytest.raises(TypeError):
            calculate_score("not a dict")

    def test_all_factors_have_weight_one(self):
        for name, weight in FACTORS:
            assert weight == 1

    def test_thresholds_ordered(self):
        """Thresholds should be in ascending order."""
        values = [t[0] for t in THRESHOLDS]
        assert values == sorted(values)


class TestAssessRow:
    """Tests for the assess_row function."""

    def test_csv_row_with_age(self):
        row = {"patient_id": "P001", "age": "68", "sex": "M"}
        r = assess_row(row)
        assert r["score"] >= 1

    def test_csv_row_low_risk(self):
        row = {"patient_id": "P002", "age": "45", "sex": "F"}
        r = assess_row(row)
        assert r["score"] == 0
        assert r["tier"] == "low"

    def test_csv_row_with_cancer(self):
        row = {"patient_id": "P003", "age": "71", "sex": "M", "cancer": "1"}
        r = assess_row(row)
        # Age>60 (1) + cancer maps to Comorbidity (1) = 2
        assert r["score"] >= 2

    def test_csv_row_all_risk_factors(self):
        row = {
            "patient_id": "P004",
            "age": "75",
            "sex": "M",
            "prior_vte": "1",
            "cancer": "1",
            "immobility": "1",
            "surgery": "1",
        }
        r = assess_row(row)
        # Age>60 + all mapped to Comorbidity (counted once) = 2
        assert r["score"] == 2

    def test_invalid_row_type(self):
        with pytest.raises(TypeError):
            assess_row("not a dict")

    def test_column_to_factor_mapping(self):
        """Verify COLUMN_TO_FACTOR has expected mappings."""
        assert COLUMN_TO_FACTOR["age"] == "Age>60"
        assert COLUMN_TO_FACTOR["cancer"] == "Comorbidity"
        assert COLUMN_TO_FACTOR["sex"] is None


class TestProcessCsv:
    """Tests for the process_csv function."""

    def test_process_sample_csv(self):
        """Process the actual sample.csv file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("patient_id,age,sex,prior_vte,cancer,immobility,surgery\n")
            f.write("P001,68,M,0,1,1,0\n")
            f.write("P002,45,F,0,0,0,1\n")
            f.write("P003,71,M,1,0,1,1\n")
            inp = f.name

        out = inp + ".out.csv"
        try:
            results = process_csv(inp, out)
            assert len(results) == 3
            assert all("score" in r for r in results)
            assert all("tier" in r for r in results)
            assert all("detail" in r for r in results)

            # Verify output file exists and has correct structure
            with open(out, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 3
                assert "score" in rows[0]
        finally:
            os.unlink(inp)
            if os.path.exists(out):
                os.unlink(out)

    def test_invalid_input_path(self):
        with pytest.raises(ValueError):
            process_csv("", "output.csv")

    def test_invalid_output_path(self):
        with pytest.raises(ValueError):
            process_csv("input.csv", "")

    def test_nonexistent_input_file(self):
        with pytest.raises(FileNotFoundError):
            process_csv("/nonexistent/path/file.csv", "output.csv")
