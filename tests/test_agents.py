import os
import sys
import unittest
import copy

# Ensure the workspace directory is in the path
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from src.common.schema_validator import validate_alert
from src.supporting_agent.orchestrator import Orchestrator
from src.common.mock_alert_generator import generate_single_mock_alert

class TestAgentComponents(unittest.TestCase):
    
    def setUp(self):
        self.orchestrator = Orchestrator()
        self.base_alert = {
            "alert_id": "ALT-20260720-00000000",
            "timestamp": "2026-07-20T10:00:00Z",
            "entity": "tcp_session_from_IP",
            "anomaly_score": 0.85,
            "features_flagged": ["serror_rate", "same_srv_rate"],
            "attack_technique": "T1498: Network Service Denial",
            "technique_confidence": 0.90,
            "response_action": "isolate_endpoint",
            "response_status": "pending_approval",
            "audit_trail": [
                {
                    "timestamp": "2026-07-20T10:00:00Z",
                    "agent": "Test Engine",
                    "action": "Unit Test Init",
                    "notes": "Testing schema validation."
                }
            ]
        }

    def test_schema_validator_valid_alert(self):
        """
        Verify that a schema-conforming alert dictionary returns True.
        """
        self.assertTrue(validate_alert(self.base_alert))

    def test_schema_validator_invalid_score_range(self):
        """
        Verify that anomaly_score outside [0.0, 1.0] raises ValueError.
        """
        bad_alert = copy.deepcopy(self.base_alert)
        bad_alert["anomaly_score"] = 1.05
        with self.assertRaises(ValueError) as ctx:
            validate_alert(bad_alert)
        self.assertIn("'anomaly_score' must be between 0.0 and 1.0", str(ctx.exception))

    def test_schema_validator_invalid_confidence_range(self):
        """
        Verify that technique_confidence outside [0.0, 1.0] raises ValueError.
        """
        bad_alert = copy.deepcopy(self.base_alert)
        bad_alert["technique_confidence"] = -0.05
        with self.assertRaises(ValueError) as ctx:
            validate_alert(bad_alert)
        self.assertIn("'technique_confidence' must be between 0.0 and 1.0", str(ctx.exception))

    def test_schema_validator_invalid_status_enum(self):
        """
        Verify that invalid response_status raises ValueError.
        """
        bad_alert = copy.deepcopy(self.base_alert)
        bad_alert["response_status"] = "malicious_status_here"
        with self.assertRaises(ValueError) as ctx:
            validate_alert(bad_alert)
        self.assertIn("'response_status' must be one of", str(ctx.exception))

    def test_orchestrator_asset_lookup(self):
        """
        Verify that orchestrator asset lookup correctly identifies criticality and CVEs.
        """
        asset = self.orchestrator.get_asset_info("tcp_session_from_IP")
        self.assertIsNotNone(asset)
        self.assertIn("criticality", asset)
        self.assertIn("ip_address", asset)

    def test_orchestrator_playbook_action_risk_score_low(self):
        """
        Verify low-risk parameters select the log_and_flag playbook.
        """
        # Low risk = low criticality (low: weight=1.0) and small anomaly score (0.1)
        # Risk score = (0.1 * 6.0) + 1.0 = 1.6
        action = self.orchestrator.select_playbook_action(asset_criticality="low", anomaly_score=0.1)
        self.assertEqual(action["name"], "log_and_flag")
        self.assertTrue(action["auto_execute"])

    def test_orchestrator_playbook_action_risk_score_critical(self):
        """
        Verify critical-risk parameters select the isolate_endpoint playbook.
        """
        # Critical risk = high criticality (critical: weight=4.0) and high anomaly score (0.9)
        # Risk score = (0.9 * 6.0) + 4.0 = 9.4 (>= 8.5)
        action = self.orchestrator.select_playbook_action(asset_criticality="critical", anomaly_score=0.9)
        self.assertEqual(action["name"], "isolate_endpoint")
        self.assertFalse(action["auto_execute"])

    def test_orchestrator_cve_boost(self):
        """
        Verify that target assets containing active CVEs receive anomaly score boosts.
        """
        # Create mock alert targeting a device
        alert = copy.deepcopy(self.base_alert)
        alert["entity"] = "database_server_cve"
        alert["anomaly_score"] = 0.50
        alert["response_status"] = "flagged"
        
        # Inject mock asset database profile with known CVEs
        self.orchestrator.assets.append({
            "entity": "database_server_cve",
            "ip_address": "10.0.0.99",
            "criticality": "high",
            "known_cves": ["CVE-2023-38606"]
        })
        
        # Orchestrate response
        enriched = self.orchestrator.orchestrate_response(alert)
        # Verify that score boost triggered higher playbook
        # Expected: anomaly_score = 0.5 + 0.1 = 0.6
        # High criticality weight = 3.0
        # Risk score = (0.6 * 6.0) + 3.0 = 6.6 (triggers rate_limit_ip instead of snapshot_vm_state)
        self.assertEqual(enriched["response_action"], "rate_limit_ip")

    def test_mock_alert_generator(self):
        """
        Verify generated mock alerts adhere to core schemas.
        """
        mock_alert = generate_single_mock_alert()
        self.assertTrue(validate_alert(mock_alert))
        self.assertIsNotNone(mock_alert["alert_id"])
        self.assertIsNotNone(mock_alert["timestamp"])

if __name__ == "__main__":
    unittest.main()
