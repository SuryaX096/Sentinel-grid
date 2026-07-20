import os
import sys
import unittest

# Ensure the workspace directory is in the path
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from src.integration.pipeline import process_flow_record, init_db, DB_PATH
from src.common.schema_validator import validate_alert

class TestAgentPipeline(unittest.TestCase):
    
    def setUp(self):
        # Ensure database is initialized
        init_db()
        
        # Test record (mock network flow)
        self.mock_flow = {
            "duration": 0.0,
            "protocol_type": "tcp",
            "service": "http",
            "flag": "SF",
            "src_bytes": 215.0,
            "dst_bytes": 4507.0,
            "land": 0,
            "wrong_fragment": 0,
            "urgent": 0,
            "hot": 0,
            "num_failed_logins": 0,
            "logged_in": 1,
            "num_compromised": 0,
            "root_shell": 0,
            "su_attempted": 0,
            "num_root": 0,
            "num_file_creations": 0,
            "num_shells": 0,
            "num_access_files": 0,
            "num_outbound_cmds": 0,
            "is_host_login": 0,
            "is_guest_login": 0,
            "count": 1.0,
            "srv_count": 1.0,
            "serror_rate": 0.0,
            "srv_serror_rate": 0.0,
            "rerror_rate": 0.0,
            "srv_rerror_rate": 0.0,
            "same_srv_rate": 1.0,
            "diff_srv_rate": 0.0,
            "srv_diff_host_rate": 0.0,
            "dst_host_count": 1.0,
            "dst_host_srv_count": 1.0,
            "dst_host_same_srv_rate": 1.0,
            "dst_host_diff_srv_rate": 0.0,
            "dst_host_same_src_port_rate": 1.0,
            "dst_host_srv_diff_host_rate": 0.0,
            "dst_host_serror_rate": 0.0,
            "dst_host_srv_serror_rate": 0.0,
            "dst_host_rerror_rate": 0.0,
            "dst_host_srv_rerror_rate": 0.0,
            "attack": "normal"
        }

    def test_database_initialization(self):
        """
        Verify that alerts.db is created.
        """
        self.assertTrue(os.path.exists(DB_PATH), "Database file alerts.db was not created.")

    def test_pipeline_execution_schema_conformance(self):
        """
        Verify that running a flow through the pipeline (online or offline fallback)
        returns a fully schema-conforming alert dict.
        """
        alert = process_flow_record(self.mock_flow)
        
        # Verify it is a dictionary
        self.assertIsInstance(alert, dict)
        
        # Verify schema compliance (will raise ValueError if invalid)
        try:
            is_valid = validate_alert(alert)
            self.assertTrue(is_valid)
        except ValueError as ve:
            self.fail(f"Pipeline output failed schema validation: {ve}")
            
    def test_pipeline_required_fields(self):
        """
        Assert presence of specific required output fields.
        """
        alert = process_flow_record(self.mock_flow)
        
        self.assertIn("alert_id", alert)
        self.assertIn("timestamp", alert)
        self.assertIn("entity", alert)
        self.assertIn("anomaly_score", alert)
        self.assertIn("features_flagged", alert)
        self.assertIn("attack_technique", alert)
        self.assertIn("technique_confidence", alert)
        self.assertIn("response_action", alert)
        self.assertIn("response_status", alert)
        self.assertIn("audit_trail", alert)

if __name__ == "__main__":
    unittest.main()
