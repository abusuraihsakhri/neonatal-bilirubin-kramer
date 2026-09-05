"""
Automated Pytest Test Suite for Neonatal Bilirubin Kramer.
Domain: Clinical & Biomedical AI
Standard: CAP / CLSI / ISO Standards
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set a test audit key before importing agents
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-key-for-unit-tests-only-32chars")

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_phi_guard_redaction():
    redacted = PHIGuard.redact_phi("Contact patient at 555-123-4567")
    assert "555-123-4567" not in redacted
    assert "[REDACTED_IDENTIFIER]" in redacted


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 1: No alert for normal values
    p1_normal = SystemTaskPayload(task_id="T1N", target_identifier="KEY-01N", primary_metric=10.0)
    alerts1_normal = InvariantQCWorker.evaluate(p1_normal)
    assert len(alerts1_normal) == 0

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 2: Secondary metric breach
    p2_sec = SystemTaskPayload(task_id="T2S", target_identifier="KEY-02S", primary_metric=10.0, secondary_metric=15.0)
    alerts2_sec = SafetyEscalationWorker.evaluate(p2_sec)
    assert len(alerts2_sec) == 1
    assert alerts2_sec[0].urgency == UrgencyLevel.ELEVATED

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1

    # Worker 3: Normal descriptor
    p3_normal = SystemTaskPayload(task_id="T3N", target_identifier="KEY-03N", primary_metric=10.0, status_descriptor="NOMINAL")
    alerts3_normal = ProtocolConformanceWorker.evaluate(p3_normal)
    assert len(alerts3_normal) == 0


def test_supervisor_consensus_and_audit():
    AuditLogger.reset()  # Start fresh
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_supervisor_critical_escalation():
    """Test that critical flags produce CRITICAL_STAT urgency."""
    AuditLogger.reset()
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-CRIT-01",
        target_identifier="KEY-CRIT-01",
        primary_metric=30.0,
        secondary_metric=15.0,
        status_descriptor="DISCORDANT_ANOMALY",
        is_critical_flag=True,
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.CRITICAL_STAT
    assert dossier.integrity_status == SystemIntegrityStatus.RECALIBRATION_REQUIRED
    assert dossier.critical_alerts_count > 0


def test_supervisor_phi_rejection():
    """Test that PHI in task_id is rejected."""
    AuditLogger.reset()
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="Patient MRN-12345",
        target_identifier="KEY-01",
        primary_metric=10.0,
    )
    with pytest.raises(SecurityException):
        supervisor.process_task(payload)


def test_audit_trail_integrity():
    """Test that audit trail detects tampering."""
    AuditLogger.reset()
    # Log some entries
    AuditLogger.log("test", "test_tier", "TEST_EVENT", {"data": "value1"})
    AuditLogger.log("test", "test_tier", "TEST_EVENT", {"data": "value2"})
    assert AuditLogger.verify_integrity() is True
    assert len(AuditLogger.get_trail()) == 2
