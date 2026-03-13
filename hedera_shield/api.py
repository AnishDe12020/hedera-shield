"""FastAPI REST API for the HederaShield compliance dashboard."""

import csv
import io
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from hedera_shield.compliance import ComplianceEngine
from hedera_shield.config import settings
from hedera_shield.enforcer import TokenEnforcer
from hedera_shield.models import (
    Alert,
    ComplianceRule,
    EnforcementAction,
    SystemStatus,
)
from hedera_shield.scanner import MirrorNodeScanner

logger = logging.getLogger(__name__)

# Shared state
scanner = MirrorNodeScanner()
compliance_engine = ComplianceEngine()
enforcer = TokenEnforcer()
_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("HederaShield API starting up")
    yield
    await scanner.close()
    logger.info("HederaShield API shutting down")


app = FastAPI(
    title="HederaShield",
    description="AI-powered on-chain compliance agent for Hedera Token Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="hedera_shield/static"), name="static")


@app.get("/")
async def dashboard():
    """Serve the main dashboard."""
    return FileResponse("hedera_shield/static/dashboard.html")


@app.get("/status", response_model=SystemStatus)
async def get_status() -> SystemStatus:
    """Get system status and summary statistics."""
    alerts = compliance_engine.get_alerts()
    unresolved = compliance_engine.get_alerts(unresolved_only=True)
    return SystemStatus(
        status="running",
        monitored_tokens=settings.monitored_token_ids,
        total_alerts=len(alerts),
        unresolved_alerts=len(unresolved),
        last_scan_at=None,
        uptime_seconds=time.time() - _start_time,
    )


@app.get("/alerts", response_model=list[Alert])
async def get_alerts(unresolved_only: bool = False) -> list[Alert]:
    """Get all compliance alerts."""
    return compliance_engine.get_alerts(unresolved_only=unresolved_only)


@app.get("/compliance/audit.csv")
async def export_compliance_audit_csv(unresolved_only: bool = False) -> Response:
    """Export compliance alerts as an audit-ready CSV."""
    alerts = compliance_engine.get_alerts(unresolved_only=unresolved_only)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "alert_id",
            "created_at",
            "resolved",
            "alert_type",
            "severity",
            "risk_score",
            "recommended_action",
            "description",
            "transaction_id",
            "token_id",
            "sender",
            "receiver",
            "amount",
            "transaction_timestamp",
        ]
    )
    for alert in alerts:
        writer.writerow(
            [
                alert.id,
                alert.created_at.isoformat(),
                alert.resolved,
                alert.alert_type.value,
                alert.severity.value,
                alert.risk_score,
                alert.recommended_action.value,
                alert.description,
                alert.transaction.transaction_id,
                alert.transaction.token_id,
                alert.transaction.sender,
                alert.transaction.receiver,
                alert.transaction.amount,
                alert.transaction.timestamp.isoformat(),
            ]
        )

    filename = "compliance_audit.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str) -> dict:
    """Mark an alert as resolved."""
    if compliance_engine.resolve_alert(alert_id):
        return {"status": "resolved", "alert_id": alert_id}
    raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")


@app.get("/rules", response_model=list[ComplianceRule])
async def get_rules() -> list[ComplianceRule]:
    """Get all compliance rules."""
    return compliance_engine.get_rules()


class RuleCreate(BaseModel):
    rule: ComplianceRule


@app.post("/rules", response_model=ComplianceRule)
async def add_rule(payload: RuleCreate) -> ComplianceRule:
    """Add a new compliance rule."""
    compliance_engine.add_rule(payload.rule)
    return payload.rule


@app.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str) -> dict:
    """Remove a compliance rule."""
    if compliance_engine.remove_rule(rule_id):
        return {"status": "deleted", "rule_id": rule_id}
    raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")


@app.get("/transactions")
async def get_transactions(token_id: str | None = None, limit: int = 50) -> dict:
    """Fetch recent transactions from the mirror node."""
    if not token_id:
        tokens = settings.monitored_token_ids
        if not tokens:
            return {"transactions": [], "message": "No tokens configured for monitoring"}
        token_id = tokens[0]

    transfers = await scanner.fetch_token_transfers(token_id, limit=limit)
    return {
        "token_id": token_id,
        "count": len(transfers),
        "transactions": [t.model_dump(mode="json") for t in transfers],
    }


class EnforceRequest(BaseModel):
    action: EnforcementAction
    token_id: str
    account_id: str


@app.post("/enforce")
async def enforce_action(req: EnforceRequest) -> dict:
    """Execute an enforcement action on an account."""
    result = await enforcer.enforce(req.action, req.token_id, req.account_id)
    return {
        "action": result.action.value,
        "target_account": result.target_account,
        "token_id": result.token_id,
        "status": result.status.value,
        "transaction_id": result.transaction_id,
        "error": result.error,
    }


@app.get("/preflight")
async def preflight_check() -> dict:
    """Run preflight diagnostics against all external dependencies."""
    from hedera_shield.preflight import run_preflight

    report = await run_preflight(settings)
    return report.to_dict()


@app.get("/health")
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "healthy"}


def start():
    """Entry point for running the API server."""
    import uvicorn
    uvicorn.run(
        "hedera_shield.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )


if __name__ == "__main__":
    start()
