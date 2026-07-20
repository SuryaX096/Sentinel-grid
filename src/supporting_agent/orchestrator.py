import os
import json
from datetime import datetime, timezone

# Define paths
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PLAYBOOKS_PATH = os.path.join(WORKSPACE_DIR, "src", "supporting_agent", "playbook_config.json")
ASSETS_PATH = os.path.join(WORKSPACE_DIR, "src", "supporting_agent", "asset_inventory.json")

class Orchestrator:
    def __init__(self):
        self.playbooks = self._load_json(PLAYBOOKS_PATH, {"actions": []})["actions"]
        self.assets = self._load_json(ASSETS_PATH, {"assets": []})["assets"]
        
    def _load_json(self, path: str, default: dict) -> dict:
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default

    def get_asset_info(self, entity: str) -> dict:
        """
        Finds the asset information corresponding to the alert entity.
        Supports exact match and prefix match.
        """
        # Exact match
        for asset in self.assets:
            if asset["entity"] == entity or asset["ip_address"] == entity:
                return asset
                
        # Prefix match (e.g., tcp_session_from_IP matches tcp_session_from_IP)
        for asset in self.assets:
            if entity.startswith(asset["entity"]) or asset["entity"].startswith(entity):
                return asset
                
        # Default fallback
        return {
            "entity": entity,
            "ip_address": "unknown",
            "criticality": "medium",
            "known_cves": []
        }

    def select_playbook_action(self, asset_criticality: str, anomaly_score: float, attack_technique: str = None) -> dict:
        """
        State machine decision engine to select the playbook action:
        - Critical assets or high-confidence anomalies require high-impact playbooks.
        - Low risk allows lower blast-radius auto-execution.
        """
        # Calculate risk score (0.0 to 10.0 scale)
        crit_weight = {"critical": 4.0, "high": 3.0, "medium": 2.0, "low": 1.0}
        weight = crit_weight.get(asset_criticality.lower(), 2.0)
        
        # Risk score combines model score and asset value
        risk_score = round((anomaly_score * 6.0) + (weight), 2)
        
        selected_action_name = "log_and_flag"
        
        # Mapping risk range to action blast radius
        if risk_score >= 8.5:
            # Critical risk: isolate the endpoint
            selected_action_name = "isolate_endpoint"
        elif risk_score >= 7.0:
            # Medium-High risk: revoke sessions
            selected_action_name = "revoke_session"
        elif risk_score >= 5.5:
            # Medium risk: rate-limit IP
            selected_action_name = "rate_limit_ip"
        elif risk_score >= 4.0:
            # Low-Medium risk: snapshot VM for analysis
            selected_action_name = "snapshot_vm_state"
        else:
            # Low risk: just log
            selected_action_name = "log_and_flag"
            
        # Retrieve action details
        for action in self.playbooks:
            if action["name"] == selected_action_name:
                return action.copy()
                
        # Fallback action
        return {
            "name": "log_and_flag",
            "description": "Log anomaly and flag for review.",
            "blast_radius": "low",
            "auto_execute": True
        }

    def orchestrate_response(self, alert: dict) -> dict:
        """
        Processes an alert and updates it with appropriate mitigation response.
        Appends a detailed log to the audit trail.
        """
        # Create a deep copy
        alert_out = alert.copy()
        
        entity = alert_out["entity"]
        anomaly_score = alert_out["anomaly_score"]
        attack_technique = alert_out.get("attack_technique")
        
        # Get target asset characteristics
        asset = self.get_asset_info(entity)
        criticality = asset["criticality"]
        known_cves = asset.get("known_cves", [])
        
        # Prioritization override: If the asset has active known CVEs, boost the effective anomaly score
        effective_score = anomaly_score
        cve_boost_applied = False
        if known_cves and alert_out["response_status"] != "normal":
            effective_score = min(1.0, anomaly_score + 0.1)
            cve_boost_applied = True
            
        # If the alert is marked normal, execute the standard log_and_flag play
        if alert_out["response_status"] == "normal":
            action = {
                "name": "log_and_flag",
                "description": "Log connection.",
                "blast_radius": "none",
                "auto_execute": True
            }
        else:
            action = self.select_playbook_action(criticality, effective_score, attack_technique)
            
        action_name = action["name"]
        auto_execute = action["auto_execute"]
        
        # Set response fields
        alert_out["response_action"] = action_name
        
        if alert_out["response_status"] == "normal":
            alert_out["response_status"] = "resolved"
            notes = "Flow classified as normal. Logged for baseline maintenance."
        else:
            if auto_execute:
                alert_out["response_status"] = "executed"
                notes = f"Auto-executed playbook '{action_name}'. Blast radius: {action['blast_radius']}."
            else:
                alert_out["response_status"] = "pending_approval"
                notes = f"Selected playbook '{action_name}' (blast radius: {action['blast_radius']}) requires human verification before execution."
                
        # Add CVE context if applicable
        if cve_boost_applied:
            notes += f" Prioritized due to active vulnerabilities on asset ({', '.join(known_cves)})."
            
        # Append to audit trail
        now_str = datetime.now(timezone.utc).isoformat()
        alert_out["audit_trail"].append({
            "timestamp": now_str,
            "agent": "Supporting Agent",
            "action": f"Mitigation Planned: {action_name.upper()}",
            "notes": notes
        })
        
        return alert_out
