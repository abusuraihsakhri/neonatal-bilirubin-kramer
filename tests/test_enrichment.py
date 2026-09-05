"""
Automated Pytest for neonatal-bilirubin-kramer Enrichment Modules.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from enrichment import (
    ThresholdEngine,
    EnrichmentResult,
    EnrichmentmdEngine,
    LongitudinalScoreTrackingEngine,
    EhrfhirIntegrationEngine,
    VisualDashboardEngine,
    AlertEscalationEngine,
    PatientStratificationEngine,
    CrossinstitutionalAnalyticsEngine,
    AutomatedReportingEngine,
    NeonatalbilirubinkramerEnrichmentSuite,
    enrichment_suite,
)


class TestThresholdEngine:
    """Tests for the base ThresholdEngine class."""

    def test_optimal_status(self):
        engine = ThresholdEngine("Test Feature", threshold=1.0)
        result = engine.evaluate(0.5)
        assert result.status == "OPTIMAL"
        assert result.score == 0.5
        assert len(result.alerts) == 0

    def test_warning_status(self):
        engine = ThresholdEngine("Test Feature", threshold=1.0)
        result = engine.evaluate(1.5)
        assert result.status == "WARNING"
        assert len(result.alerts) == 1

    def test_critical_alert_status(self):
        engine = ThresholdEngine("Test Feature", threshold=1.0)
        result = engine.evaluate(3.0)
        assert result.status == "CRITICAL_ALERT"
        assert len(result.alerts) == 1

    def test_history_tracking(self):
        engine = ThresholdEngine("Test Feature", threshold=1.0)
        engine.evaluate(0.5)
        engine.evaluate(1.5)
        assert len(engine.history) == 2

    def test_feature_name_preserved(self):
        engine = ThresholdEngine("Custom Feature Name", threshold=1.0)
        result = engine.evaluate(0.5)
        assert result.feature_name == "Custom Feature Name"


class TestNamedEngines:
    """Tests that named engines inherit from ThresholdEngine correctly."""

    def test_enrichmentmd_engine(self):
        engine = EnrichmentmdEngine(threshold=2.0)
        assert engine.feature_name == "specifications"
        result = engine.evaluate(1.0)
        assert result.status == "OPTIMAL"

    def test_longitudinal_engine(self):
        engine = LongitudinalScoreTrackingEngine(threshold=2.0)
        assert engine.feature_name == "Longitudinal Score Tracking"

    def test_ehrfhir_engine(self):
        engine = EhrfhirIntegrationEngine(threshold=2.0)
        assert engine.feature_name == "EHR/FHIR Integration"

    def test_visual_dashboard_engine(self):
        engine = VisualDashboardEngine(threshold=2.0)
        assert engine.feature_name == "Visual Dashboard"

    def test_alert_escalation_engine(self):
        engine = AlertEscalationEngine(threshold=2.0)
        assert engine.feature_name == "Alert Escalation"

    def test_patient_stratification_engine(self):
        engine = PatientStratificationEngine(threshold=2.0)
        assert engine.feature_name == "Patient Stratification"

    def test_crossinstitutional_engine(self):
        engine = CrossinstitutionalAnalyticsEngine(threshold=2.0)
        assert engine.feature_name == "Cross-Institutional Analytics"

    def test_automated_reporting_engine(self):
        engine = AutomatedReportingEngine(threshold=2.0)
        assert engine.feature_name == "Automated Reporting"


def test_enrichment_suite_execution():
    suite = NeonatalbilirubinkramerEnrichmentSuite()
    res = suite.execute_all(primary_val=0.5, secondary_val=0.2)
    assert len(res) == 8  # All 8 engines
    for k, v in res.items():
        assert v.status in ["OPTIMAL", "WARNING", "CRITICAL_ALERT"]
        assert isinstance(v.recommendations, list)

def test_enrichment_threshold_escalation():
    suite = NeonatalbilirubinkramerEnrichmentSuite()
    res = suite.execute_all(primary_val=10.0, secondary_val=5.0)
    for k, v in res.items():
        assert v.status in ["WARNING", "CRITICAL_ALERT"]
        assert len(v.alerts) > 0

def test_enrichment_suite_with_custom_threshold():
    suite = NeonatalbilirubinkramerEnrichmentSuite(threshold=5.0)
    res = suite.execute_all(primary_val=3.0, secondary_val=1.0)
    for k, v in res.items():
        assert v.status == "OPTIMAL"

def test_global_enrichment_suite():
    """Test the global enrichment_suite instance."""
    res = enrichment_suite.execute_all(primary_val=0.1)
    assert len(res) == 8
