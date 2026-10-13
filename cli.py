"""
Command Line Interface for Neonatal Bilirubin Kramer.
"""
import argparse
import csv
import json
import sys
from pathlib import Path
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.base import AuditLogger

supervisor = SystemSupervisor(model_provider="mock")


def parse_boolean(value):
    """Parse CSV booleans explicitly; bool("false") is True in Python."""
    if isinstance(value, bool):
        return value
    if value is None or str(value).strip().lower() in ("", "0", "false", "no", "n"):
        return False
    if str(value).strip().lower() in ("1", "true", "yes", "y"):
        return True
    raise ValueError(f"Invalid boolean value: {value!r}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="neonatal-bilirubin-kramer", description="Neonatal Bilirubin Kramer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="KEY-TARGET-01")
    p_audit.add_argument("--primary", type=float, default=28.5)
    p_audit.add_argument("--secondary", type=float, default=14.2)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Verify Audit
    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("=" * 80)
        print(f"  NEONATAL BILIRUBIN KRAMER")
        print("  Demonstration-only rules; not clinical bilirubin guidance")
        print(f"  Dossier ID: {dossier.dossier_id} | Urgency: [{dossier.overall_urgency.value}]")
        print("=" * 80)
        for a in dossier.alerts:
            print(f"\n  [{a.urgency.value}] from {a.origin_worker}:")
            print(f"  Summary: {a.summary}")
            print(f"  Details: {a.technical_details}")
            print(f"  Action:  {a.actionable_remediation}")
        print(f"\n  HMAC-SHA256 Audit Hash: {dossier.audit_hash}")
        print("=" * 80)
        return 0

    if args.command == "chat":
        ans = supervisor.query_supervisory_chat(" ".join(args.query))
        print(f"\n[Neonatal Bilirubin Kramer Supervisor]:\n{ans}\n")
        return 0

    if args.command == "verify-audit":
        trail = AuditLogger.get_trail()
        valid = AuditLogger.verify_integrity()
        print(f"Audit Trail Blocks: {len(trail)} | Cryptographic Integrity Verified: {valid}")
        return 0

    if args.command == "batch":
        if Path(args.input).resolve() == Path(args.output).resolve():
            raise ValueError("Input and output paths must differ")
        if Path(args.input).stat().st_size > 10 * 1024 * 1024:
            raise ValueError("Batch input must not exceed 10 MiB")
        with open(args.input, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            if not fieldnames or len(set(fieldnames)) != len(fieldnames):
                raise ValueError("CSV requires a header with unique field names")
            rows = list(reader)
        computed = ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]
        if set(fieldnames).intersection(computed):
            raise ValueError("CSV input must not contain reserved output fields")
        out_fields = fieldnames + computed
        out_rows = []
        for line_number, r in enumerate(rows, start=2):
            if None in r:
                raise ValueError(f"Unexpected additional CSV values on line {line_number}")
            payload = SystemTaskPayload(
                task_id=r.get("task_id", "TASK-01"),
                target_identifier=r.get("target_identifier", "TARGET-01"),
                primary_metric=float(r.get("primary_metric", 15.0)),
                secondary_metric=float(r.get("secondary_metric", 5.0)),
                status_descriptor=r.get("status_descriptor", "NOMINAL"),
                is_critical_flag=parse_boolean(r.get("is_critical_flag", False)),
            )
            dossier = supervisor.process_task(payload)
            row_dict = dict(r)
            row_dict["overall_urgency"] = dossier.overall_urgency.value
            row_dict["integrity_status"] = dossier.integrity_status.value
            row_dict["total_alerts"] = dossier.total_alerts
            row_dict["audit_hash"] = dossier.audit_hash
            out_rows.append(row_dict)

        with open(args.output, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Processed {len(out_rows)} records -> {args.output}")
        return 0

    if args.command == "serve":
        import uvicorn
        from agents.api import app
        print(f"Starting Neonatal Bilirubin Kramer API server on http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
