import os
import json
import sqlite3
import requests
from datetime import datetime, timezone
from src.common.schema_validator import validate_alert

# Agent API URLs
HERO_API_URL = "http://127.0.0.1:8001/detect"
ATTRIBUTION_API_URL = "http://127.0.0.1:8002/attribute"
SUPPORTING_API_URL = "http://127.0.0.1:8003/respond"

# Define paths
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(WORKSPACE_DIR, "alerts.db")

def init_db():
    """
    Initializes the SQLite database to store pipeline alerts.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                timestamp TEXT,
                entity TEXT,
                anomaly_score REAL,
                features_flagged TEXT,
                attack_technique TEXT,
                technique_confidence REAL,
                response_action TEXT,
                response_status TEXT,
                audit_trail TEXT
            )
        """)
        conn.commit()

# Initialize DB once on module load
try:
    init_db()
except Exception as e:
    print(f"WARNING: Database initialization failed: {e}")

def save_alert_to_db(alert: dict):
    """
    Saves or updates an alert in the SQLite database.
    """
    # Convert lists/dicts to JSON strings for SQLite storage
    features_flagged_str = json.dumps(alert.get("features_flagged", []))
    audit_trail_str = json.dumps(alert.get("audit_trail", []))
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO alerts (
                alert_id, timestamp, entity, anomaly_score, features_flagged,
                attack_technique, technique_confidence, response_action, response_status, audit_trail
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert["alert_id"],
            alert["timestamp"],
            alert["entity"],
            float(alert["anomaly_score"]),
            features_flagged_str,
            alert.get("attack_technique"),
            float(alert["technique_confidence"]) if alert.get("technique_confidence") is not None else None,
            alert.get("response_action"),
            alert["response_status"],
            audit_trail_str
        ))
        conn.commit()

def process_flow_record(flow_record: dict) -> dict:
    """
    Runs a single network flow record through the entire Agent Pipeline.
    1. Hero Agent (detects anomaly)
    2. Attribution Agent (attributes to MITRE technique)
    3. Supporting Agent (plans response playbook)
    Stores results in SQLite database.
    """
    try:
        # Step 1: Detect Anomaly (Hero Agent)
        # Note: If API is offline, requests will raise a ConnectionError which we handle
        detect_resp = requests.post(HERO_API_URL, json=flow_record, timeout=5)
        if detect_resp.status_code != 200:
            raise RuntimeError(f"Hero Agent returned status code {detect_resp.status_code}: {detect_resp.text}")
            
        detect_data = detect_resp.json()
        alert = detect_data["alert"]
        is_anomaly = detect_data["is_anomaly"]
        
        # Step 2: Attribute Threat (Attribution Agent) - skip/default if normal
        if is_anomaly:
            attr_resp = requests.post(ATTRIBUTION_API_URL, json=alert, timeout=10)
            if attr_resp.status_code == 200:
                alert = attr_resp.json()
            else:
                print(f"WARNING: Attribution Agent error: {attr_resp.text}. Proceeding with raw alert.")
        else:
            alert["attack_technique"] = "None"
            alert["technique_confidence"] = 0.0
            
        # Step 3: Plan Automated Response (Supporting Agent)
        respond_resp = requests.post(SUPPORTING_API_URL, json=alert, timeout=5)
        if respond_resp.status_code == 200:
            alert = respond_resp.json()
        else:
            print(f"WARNING: Supporting Agent error: {respond_resp.text}. Proceeding with current alert state.")
            
        # Validate schema before persisting
        validate_alert(alert)
        
        # Step 4: Persist alert to database
        save_alert_to_db(alert)
        
        return alert
        
    except requests.exceptions.ConnectionError as ce:
        print(f"Pipeline Connection Error: Ensure all agent services are running on ports 8001, 8002, 8003. Details: {ce}")
        # Return a mock schema-compliant alert indicating connection failure
        now_str = datetime.now(timezone.utc).isoformat()
        fail_alert = {
            "alert_id": f"ALT-ERR-{int(datetime.now(timezone.utc).timestamp())}",
            "timestamp": now_str,
            "entity": str(flow_record.get("protocol_type", "unknown")) + "_session_from_IP",
            "anomaly_score": 0.0,
            "features_flagged": [],
            "attack_technique": "Error: Agent Offline",
            "technique_confidence": 0.0,
            "response_action": "alert_ops_team",
            "response_status": "pipeline_error",
            "audit_trail": [
                {
                    "timestamp": now_str,
                    "agent": "Integration Pipeline",
                    "action": "Execution Failed",
                    "notes": f"Unable to reach agent microservices. Connection failed: {ce}"
                }
            ]
        }
        save_alert_to_db(fail_alert)
        return fail_alert

    except requests.exceptions.Timeout as te:
        print(f"Pipeline Timeout Error: Agent service did not respond within timeout. Details: {te}")
        now_str = datetime.now(timezone.utc).isoformat()
        fail_alert = {
            "alert_id": f"ALT-TMO-{int(datetime.now(timezone.utc).timestamp())}",
            "timestamp": now_str,
            "entity": str(flow_record.get("protocol_type", "unknown")) + "_session_from_IP",
            "anomaly_score": 0.0,
            "features_flagged": [],
            "attack_technique": "Error: Agent Timeout",
            "technique_confidence": 0.0,
            "response_action": "alert_ops_team",
            "response_status": "pipeline_error",
            "audit_trail": [
                {
                    "timestamp": now_str,
                    "agent": "Integration Pipeline",
                    "action": "Execution Timed Out",
                    "notes": f"Agent microservice did not respond within timeout: {te}"
                }
            ]
        }
        save_alert_to_db(fail_alert)
        return fail_alert

    except Exception as ex:
        print(f"Pipeline Unexpected Error: {ex}")
        now_str = datetime.now(timezone.utc).isoformat()
        fail_alert = {
            "alert_id": f"ALT-UNK-{int(datetime.now(timezone.utc).timestamp())}",
            "timestamp": now_str,
            "entity": str(flow_record.get("protocol_type", "unknown")) + "_session_from_IP",
            "anomaly_score": 0.0,
            "features_flagged": [],
            "attack_technique": "Error: Unexpected Failure",
            "technique_confidence": 0.0,
            "response_action": "alert_ops_team",
            "response_status": "pipeline_error",
            "audit_trail": [
                {
                    "timestamp": now_str,
                    "agent": "Integration Pipeline",
                    "action": "Unexpected Error",
                    "notes": f"Pipeline encountered an unexpected error: {ex}"
                }
            ]
        }
        save_alert_to_db(fail_alert)
        return fail_alert

if __name__ == "__main__":
    # Test connection checks
    init_db()
    print("Integration Database initialized at", DB_PATH)
