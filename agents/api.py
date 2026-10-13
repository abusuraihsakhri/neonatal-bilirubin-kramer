"""
FastAPI REST API Server for Neonatal Bilirubin Kramer.
"""
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .base import AuditLogger, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Neonatal Bilirubin Kramer API",
    description="Demonstration-only software interface; no validated neonatal bilirubin decision support.",
    version="0.2.0",
)


class ChatRequest(BaseModel):
    query: str


ROOT = Path(__file__).resolve().parent.parent


@app.get("/", include_in_schema=False)
def homepage():
    return FileResponse(ROOT / "index.html", media_type="text/html")


@app.get("/styles.css", include_in_schema=False)
def style_asset():
    return FileResponse(ROOT / "styles.css", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def javascript_asset():
    return FileResponse(ROOT / "app.js", media_type="application/javascript")


@app.get("/health")
def health():
    return {
        "status": "HEALTHY",
        "service": "neonatal-bilirubin-kramer",
        "mode": "demonstration-not-clinical",
        "version": "0.2.0",
    }


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        return supervisor.process_task(payload).to_dict()
    except SecurityException as exc:
        raise HTTPException(status_code=422, detail="Potential personal identifier in input") from exc


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException as exc:
        raise HTTPException(status_code=422, detail="Potential personal identifier in input") from exc


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
