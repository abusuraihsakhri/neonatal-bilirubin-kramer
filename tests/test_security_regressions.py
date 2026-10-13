"""Security and parsing regressions."""
import pytest

from agents.base import AuditTrail
from agents.models import SystemTaskPayload
from cli import parse_boolean


def test_hmac_detects_mutation_in_signed_entry():
    trail = AuditTrail(secret_key="unit-test-key-not-production-secret-012345")
    trail.log("tester", "test", "event", {"count": 1})
    assert trail.verify_integrity()
    trail.logs[0]["event_type"] = "forged"
    assert not trail.verify_integrity()


def test_hmac_detects_mutation_in_last_entry():
    trail = AuditTrail(secret_key="unit-test-key-not-production-secret-012345")
    trail.log("tester", "test", "first", {"count": 1})
    trail.log("tester", "test", "second", {"count": 2})
    trail.logs[-1]["payload_hash"] = "0" * 64
    assert not trail.verify_integrity()


def test_audit_trail_is_defensive_copy():
    trail = AuditTrail(secret_key="unit-test-key-not-production-secret-012345")
    trail.log("tester", "test", "event", {"count": 1})
    trail.get_trail()[0]["event_type"] = "forged"
    assert trail.verify_integrity()


def test_csv_boolean_parser():
    assert parse_boolean("false") is False
    assert parse_boolean("0") is False
    assert parse_boolean("True") is True
    assert parse_boolean("yes") is True
    with pytest.raises(ValueError):
        parse_boolean("unknown")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_pydantic_rejects_nonfinite_metrics(value):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="T", target_identifier="K", primary_metric=value)


def test_unknown_model_provider_never_claims_external_inference():
    from agents.llm_factory import LLMFactory
    with pytest.raises(ValueError, match="not implemented"):
        LLMFactory.create("openai")


def test_enrichment_rejects_nonfinite_and_invalid_thresholds():
    from enrichment import ThresholdEngine
    with pytest.raises(ValueError):
        ThresholdEngine("demo", threshold=0)
    with pytest.raises(ValueError):
        ThresholdEngine("demo", threshold=float("nan"))
    engine = ThresholdEngine("demo", threshold=1)
    with pytest.raises(ValueError):
        engine.evaluate(float("inf"))


def test_simulator_rejects_zero_tasks():
    from simulator import run_simulation
    with pytest.raises(ValueError):
        run_simulation(0)
