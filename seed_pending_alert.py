import sqlite3
import json
import uuid
from datetime import datetime, timezone

conn = sqlite3.connect("alerts.db")
now = datetime.now(timezone.utc).isoformat()

alert_id = f"ALT-DEMO-{uuid.uuid4().hex[:8]}"
audit_trail = [
    {
        "timestamp": now,
        "agent": "Hero Agent",
        "action": "Analysis Complete",
        "notes": "Flow record analyzed. Classification: ANOMALY. Score: 0.9300.",
    },
    {
        "timestamp": now,
        "agent": "Attribution Agent",
        "action": "Threat Attributed",
        "notes": "Attributed threat to MITRE technique 'T1498 (Network Service Denial)' with confidence 0.81.",
    },
    {
        "timestamp": now,
        "agent": "Supporting Agent",
        "action": "Mitigation Planned: ISOLATE_ENDPOINT",
        "notes": "Selected playbook 'isolate_endpoint' (blast radius: high) requires human verification before execution.",
    },
]

conn.execute(
    """INSERT INTO alerts
       (alert_id, timestamp, entity, anomaly_score, features_flagged,
        attack_technique, technique_confidence, response_action, response_status, audit_trail)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    (
        alert_id, now, "scada_gateway_04", 0.93,
        json.dumps(["dst_host_srv_serror_rate", "src_bytes", "connection frequency ratio"]),
        "T1498: Network Service Denial", 0.81, "isolate_endpoint",
        "pending_approval", json.dumps(audit_trail),
    ),
)
conn.commit()
conn.close()
print(f"Seeded one pending_approval alert: {alert_id}")