"""
Enrichment Feature Implementation for neonatal-bilirubin-kramer.
Threshold-based monitoring engines for clinical decision support.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import datetime
import math


@dataclass
class EnrichmentResult:
    """Result from a threshold-based enrichment engine."""
    feature_name: str
    status: str = "OPTIMAL"
    score: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class ThresholdEngine:
    """Generic threshold-based monitoring engine.

    Evaluates a primary value against configurable thresholds to produce
    status, alerts, and recommendations.
    """

    def __init__(self, feature_name: str, threshold: float = 1.0, config: Optional[Dict[str, Any]] = None):
        threshold = float(threshold)
        if not math.isfinite(threshold) or threshold <= 0:
            raise ValueError("Demonstration threshold must be finite and > 0")
        self.feature_name = feature_name
        self.threshold = threshold
        self.config = config or {}
        self.history: List[EnrichmentResult] = []

    def evaluate(self, primary_value: float, secondary_value: float = 0.0, **kwargs) -> EnrichmentResult:
        """Evaluate primary value against thresholds.

        Args:
            primary_value: The primary metric to evaluate
            secondary_value: Optional secondary metric for context
            **kwargs: Additional metrics stored in result

        Returns:
            EnrichmentResult with status, alerts, and recommendations
        """
        primary_value = float(primary_value)
        secondary_value = float(secondary_value)
        if not math.isfinite(primary_value) or not math.isfinite(secondary_value):
            raise ValueError("Metrics must be finite numeric values")
        alerts = []
        recs = []
        status = "OPTIMAL"
        score = round(primary_value, 3)

        if primary_value > self.threshold * 2:
            status = "CRITICAL_ALERT"
            alerts.append(
                f"{self.feature_name}: Primary value {primary_value:.2f} "
                f"breached critical threshold ({self.threshold * 2:.2f})"
            )
            recs.append("Review demonstration threshold configuration; no clinical action is inferred.")
        elif primary_value > self.threshold:
            status = "WARNING"
            alerts.append(
                f"{self.feature_name}: Value {primary_value:.2f} "
                f"exceeds baseline threshold ({self.threshold:.2f})"
            )
            recs.append("Review demonstration values; no clinical action is inferred.")
        else:
            recs.append("Value is within the configured illustrative bounds (not a clinical range).")

        res = EnrichmentResult(
            feature_name=self.feature_name,
            status=status,
            score=score,
            metrics={"primary": primary_value, "secondary": secondary_value, **kwargs},
            alerts=alerts,
            recommendations=recs,
        )
        self.history.append(res)
        return res


# Named engine instances for each domain feature
class EnrichmentmdEngine(ThresholdEngine):
    def __init__(self, threshold: float = 1.0, config: Optional[Dict[str, Any]] = None):
        super().__init__("specifications", threshold, config)


class LongitudinalScoreTrackingEngine(ThresholdEngine):
    def __init__(self, threshold: float = 1.0, config: Optional[Dict[str, Any]] = None):
        super().__init__("Longitudinal Score Tracking", threshold, config)


class EhrfhirIntegrationEngine(ThresholdEngine):
    def __init__(self, threshold: float = 1.0, config: Optional[Dict[str, Any]] = None):
        super().__init__("EHR/FHIR Integration", threshold, config)


class VisualDashboardEngine(ThresholdEngine):
    def __init__(self, threshold: float = 1.0, config: Optional[Dict[str, Any]] = None):
        super().__init__("Visual Dashboard", threshold, config)


class AlertEscalationEngine(ThresholdEngine):
    def __init__(self, threshold: float = 1.0, config: Optional[Dict[str, Any]] = None):
        super().__init__("Alert Escalation", threshold, config)


class PatientStratificationEngine(ThresholdEngine):
    def __init__(self, threshold: float = 1.0, config: Optional[Dict[str, Any]] = None):
        super().__init__("Patient Stratification", threshold, config)


class CrossinstitutionalAnalyticsEngine(ThresholdEngine):
    def __init__(self, threshold: float = 1.0, config: Optional[Dict[str, Any]] = None):
        super().__init__("Cross-Institutional Analytics", threshold, config)


class AutomatedReportingEngine(ThresholdEngine):
    def __init__(self, threshold: float = 1.0, config: Optional[Dict[str, Any]] = None):
        super().__init__("Automated Reporting", threshold, config)


# Backwards-compatible result dataclasses (deprecated, use EnrichmentResult)
EnrichmentmdEngineResult = EnrichmentResult
LongitudinalScoreTrackingEngineResult = EnrichmentResult
EhrfhirIntegrationEngineResult = EnrichmentResult
VisualDashboardEngineResult = EnrichmentResult
AlertEscalationEngineResult = EnrichmentResult
PatientStratificationEngineResult = EnrichmentResult
CrossinstitutionalAnalyticsEngineResult = EnrichmentResult
AutomatedReportingEngineResult = EnrichmentResult


# =============================================================================
# COMPOSITE ENRICHMENT SUITE
# =============================================================================
class NeonatalbilirubinkramerEnrichmentSuite:
    """Master coordinator executing all enriched domain features."""

    ENGINE_NAMES = [
        "EnrichmentmdEngine",
        "LongitudinalScoreTrackingEngine",
        "EhrfhirIntegrationEngine",
        "VisualDashboardEngine",
        "AlertEscalationEngine",
        "PatientStratificationEngine",
        "CrossinstitutionalAnalyticsEngine",
        "AutomatedReportingEngine",
    ]

    def __init__(self, threshold: float = 1.0):
        self.enrichmentmdengine = EnrichmentmdEngine(threshold=threshold)
        self.longitudinalscoretra = LongitudinalScoreTrackingEngine(threshold=threshold)
        self.ehrfhirintegrationen = EhrfhirIntegrationEngine(threshold=threshold)
        self.visualdashboardengin = VisualDashboardEngine(threshold=threshold)
        self.alertescalationengin = AlertEscalationEngine(threshold=threshold)
        self.patientstratificatio = PatientStratificationEngine(threshold=threshold)
        self.crossinstitutionalan = CrossinstitutionalAnalyticsEngine(threshold=threshold)
        self.automatedreportingen = AutomatedReportingEngine(threshold=threshold)

    def execute_all(self, primary_val: float = 1.5, secondary_val: float = 0.5) -> Dict[str, EnrichmentResult]:
        """Execute all enrichment engines and return results."""
        results = {}
        for name in self.ENGINE_NAMES:
            engine = getattr(self, _engine_attr_name(name))
            results[name] = engine.evaluate(primary_val, secondary_val)
        return results


def _engine_attr_name(class_name: str) -> str:
    """Convert class name to the attribute name used in the suite."""
    mapping = {
        "EnrichmentmdEngine": "enrichmentmdengine",
        "LongitudinalScoreTrackingEngine": "longitudinalscoretra",
        "EhrfhirIntegrationEngine": "ehrfhirintegrationen",
        "VisualDashboardEngine": "visualdashboardengin",
        "AlertEscalationEngine": "alertescalationengin",
        "PatientStratificationEngine": "patientstratificatio",
        "CrossinstitutionalAnalyticsEngine": "crossinstitutionalan",
        "AutomatedReportingEngine": "automatedreportingen",
    }
    return mapping[class_name]


# Global instance
enrichment_suite = NeonatalbilirubinkramerEnrichmentSuite()
