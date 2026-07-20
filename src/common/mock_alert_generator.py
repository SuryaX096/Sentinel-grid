import random
import uuid
from datetime import datetime, timezone, timedelta
from src.common.schema_validator import validate_alert

def generate_single_mock_alert(index: int = 1) -> dict:
    """
    Generates a single mock alert conforming to the alert schema.
    """
    entities = [
        "192.168.1.105", 
        "192.168.1.150", 
        "database-prod-01.internal", 
        "api-gateway-web", 
        "10.0.0.4",
        "workstation-hr-12",
        "10.0.2.15"
    ]
    
    anomalous_features_pool = [
        "duration", "src_bytes", "dst_bytes", "wrong_fragment", 
        "hot", "num_failed_logins", "logged_in", "count", 
        "srv_count", "serror_rate", "srv_serror_rate", 
        "rerror_rate", "dst_host_count", "dst_host_srv_count", 
        "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate"
    ]
    
    entity = random.choice(entities)
    anomaly_score = round(random.uniform(0.65, 0.98), 3)
    num_features = random.randint(2, 5)
    features_flagged = random.sample(anomalous_features_pool, num_features)
    
    # Calculate a offset timestamp
    now = datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 120))
    timestamp_str = now.isoformat()
    
    alert = {
      "alert_id": f"ALT-{now.strftime('%Y%m%d')}-{index:03d}-{str(uuid.uuid4())[:8]}",
      "timestamp": timestamp_str,
      "entity": entity,
      "anomaly_score": anomaly_score,
      "features_flagged": features_flagged,
      "attack_technique": None,
      "technique_confidence": None,
      "response_action": None,
      "response_status": "pending",
      "audit_trail": [
          {
              "timestamp": timestamp_str,
              "agent": "Hero Agent",
              "action": "Anomaly Detected",
              "notes": f"Detected outlier flow with {', '.join(features_flagged)}. Anomaly score: {anomaly_score}."
          }
      ]
    }
    
    # Validate to ensure correctness
    validate_alert(alert)
    return alert

def generate_mock_alerts(count: int = 12) -> list:
    """
    Generates a list of mock alerts.
    """
    return [generate_single_mock_alert(i + 1) for i in range(count)]

if __name__ == "__main__":
    alerts = generate_mock_alerts(5)
    print(f"Generated {len(alerts)} mock alerts successfully!")
    print(f"Sample alert:\n{alerts[0]}")
