def validate_alert(alert_dict: dict) -> bool:
    """
    Validates a dictionary against the alert schema requirements.
    Raises ValueError if validation fails.
    """
    required_keys = [
        "alert_id",
        "timestamp",
        "entity",
        "anomaly_score",
        "features_flagged",
        "attack_technique",
        "technique_confidence",
        "response_action",
        "response_status",
        "audit_trail"
    ]
    
    # Check key presence
    for key in required_keys:
        if key not in alert_dict:
            raise ValueError(f"Validation Error: Missing required key '{key}'")
            
    # Check types
    if not isinstance(alert_dict["alert_id"], str):
        raise ValueError(f"Validation Error: 'alert_id' must be a string, got {type(alert_dict['alert_id']).__name__}")
        
    if not isinstance(alert_dict["timestamp"], str):
        raise ValueError(f"Validation Error: 'timestamp' must be a string, got {type(alert_dict['timestamp']).__name__}")
        
    if not isinstance(alert_dict["entity"], str):
        raise ValueError(f"Validation Error: 'entity' must be a string, got {type(alert_dict['entity']).__name__}")
        
    if not isinstance(alert_dict["anomaly_score"], (int, float)):
        raise ValueError(f"Validation Error: 'anomaly_score' must be a number, got {type(alert_dict['anomaly_score']).__name__}")
        
    if not isinstance(alert_dict["features_flagged"], list):
        raise ValueError(f"Validation Error: 'features_flagged' must be a list, got {type(alert_dict['features_flagged']).__name__}")
        
    for idx, feature in enumerate(alert_dict["features_flagged"]):
        if not isinstance(feature, str):
            raise ValueError(f"Validation Error: 'features_flagged' item at index {idx} must be a string")
        
    if alert_dict["attack_technique"] is not None and not isinstance(alert_dict["attack_technique"], str):
        raise ValueError(f"Validation Error: 'attack_technique' must be a string or None")
        
    if alert_dict["technique_confidence"] is not None and not isinstance(alert_dict["technique_confidence"], (int, float)):
        raise ValueError(f"Validation Error: 'technique_confidence' must be a number or None")
        
    if alert_dict["response_action"] is not None and not isinstance(alert_dict["response_action"], str):
        raise ValueError(f"Validation Error: 'response_action' must be a string or None")
        
    if not isinstance(alert_dict["response_status"], str):
        raise ValueError(f"Validation Error: 'response_status' must be a string, got {type(alert_dict['response_status']).__name__}")
        
    if not isinstance(alert_dict["audit_trail"], list):
        raise ValueError(f"Validation Error: 'audit_trail' must be a list, got {type(alert_dict['audit_trail']).__name__}")
        
    for idx, audit in enumerate(alert_dict["audit_trail"]):
        if not isinstance(audit, dict):
            raise ValueError(f"Validation Error: 'audit_trail' item at index {idx} must be a dictionary")
        audit_required = ["timestamp", "agent", "action", "notes"]
        for ak in audit_required:
            if ak not in audit:
                raise ValueError(f"Validation Error: Missing audit trail key '{ak}' in item at index {idx}")
            if not isinstance(audit[ak], str):
                raise ValueError(f"Validation Error: Audit trail key '{ak}' at index {idx} must be a string")
                
    return True
