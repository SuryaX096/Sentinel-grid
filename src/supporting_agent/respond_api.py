import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.common.schema_validator import validate_alert
from src.supporting_agent.orchestrator import Orchestrator

app = FastAPI(title="Supporting Agent - Playbook Response API")
orchestrator = Orchestrator()

from typing import Optional

# Reuse schema validator types for request
class AlertPayload(BaseModel):
    alert_id: str
    timestamp: str
    entity: str
    anomaly_score: float
    features_flagged: list
    attack_technique: Optional[str] = None
    technique_confidence: Optional[float] = None
    response_action: Optional[str] = None
    response_status: str
    audit_trail: list

class ApprovalPayload(BaseModel):
    alert: AlertPayload
    approved: bool
    analyst_name: str = "SOC Analyst"
    notes: str = "Approved from security management console."

@app.post("/respond")
def plan_mitigation(alert: AlertPayload):
    try:
        alert_dict = alert.model_dump()
        # Run orchestration
        enriched_alert = orchestrator.orchestrate_response(alert_dict)
        # Validate output schema
        validate_alert(enriched_alert)
        return enriched_alert
    except Exception as e:
        print(f"Orchestration failed: {e}")
        raise HTTPException(status_code=400, detail="Orchestration failed due to an internal processing error.")

@app.post("/approve")
def approve_mitigation(payload: ApprovalPayload):
    alert_dict = payload.alert.model_dump()
    
    if alert_dict["response_status"] != "pending_approval":
        raise HTTPException(status_code=400, detail="Alert status is invalid for approval.")
        
    now_str = datetime.now(timezone.utc).isoformat()
    
    if payload.approved:
        action_name = alert_dict["response_action"]
        alert_dict["response_status"] = "executed"
        audit_note = f"Action Approved: Playbook '{action_name}' executed. Decision by {payload.analyst_name}. Rationale: {payload.notes}."
        action_title = f"Manual Approval: {action_name.upper()}"
    else:
        alert_dict["response_status"] = "dismissed"
        audit_note = f"Action Rejected: Playbook execution cancelled. Dismissed by {payload.analyst_name}. Rationale: {payload.notes}."
        action_title = "Manual Override: REJECTED"
        
    alert_dict["audit_trail"].append({
        "timestamp": now_str,
        "agent": "Supporting Agent (Gated Console)",
        "action": action_title,
        "notes": audit_note
    })
    
    # Re-validate
    validate_alert(alert_dict)
    return alert_dict

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)
