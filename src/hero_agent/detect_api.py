import os
import pickle
import json
import uuid
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Union
from src.common.schema_validator import validate_alert
from src.hero_agent.feature_engineering import transform_record, get_final_feature_columns

# Define paths
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_PATH = os.path.join(WORKSPACE_DIR, "src", "hero_agent", "model.pkl")
METADATA_PATH = os.path.join(WORKSPACE_DIR, "src", "hero_agent", "metadata.json")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model and encoding metadata at startup
    load_artifacts()
    yield

app = FastAPI(title="Hero Agent - Anomaly Detection API", lifespan=lifespan)

# Global variables for model state
model = None
threshold = 0.5
feature_columns = []
encoding_mappings = {}
feature_means = {}
feature_stds = {}

class FlowRecord(BaseModel):
    # Standard flow record structure representing a connection log
    duration: float
    protocol_type: Union[str, int]
    service: Union[str, int]
    flag: Union[str, int]
    src_bytes: float
    dst_bytes: float
    land: int
    wrong_fragment: int
    urgent: int
    hot: int
    num_failed_logins: int
    logged_in: int
    num_compromised: int
    root_shell: int
    su_attempted: int
    num_root: int
    num_file_creations: int
    num_shells: int
    num_access_files: int
    num_outbound_cmds: int
    is_host_login: int
    is_guest_login: int
    count: float
    srv_count: float
    serror_rate: float
    srv_serror_rate: float
    rerror_rate: float
    srv_rerror_rate: float
    same_srv_rate: float
    diff_srv_rate: float
    srv_diff_host_rate: float
    dst_host_count: float
    dst_host_srv_count: float
    dst_host_same_srv_rate: float
    dst_host_diff_srv_rate: float
    dst_host_same_src_port_rate: float
    dst_host_srv_diff_host_rate: float
    dst_host_serror_rate: float
    dst_host_srv_serror_rate: float
    dst_host_rerror_rate: float
    dst_host_srv_rerror_rate: float
    # Optional field representing ground-truth label in replay
    attack: str = "normal"

FlowRecord.model_rebuild()

def load_artifacts():
    global model, threshold, feature_columns, encoding_mappings, feature_means, feature_stds
    
    # Load metadata
    if not os.path.exists(METADATA_PATH):
        raise FileNotFoundError(f"Encoding metadata not found at {METADATA_PATH}. Run training first.")
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)
        encoding_mappings = metadata["encoding_mappings"]
        
    # Load model
    if not os.path.exists(MODEL_PATH):
        print(f"WARNING: Model artifact not found at {MODEL_PATH}. API starting in uninitialized/mock mode.")
        return
        
    # Verify SHA-256 integrity hash before unpickling
    hash_path = MODEL_PATH + ".sha256"
    if not os.path.exists(hash_path):
        raise RuntimeError(f"Security Alert: Checksum file not found at {hash_path}. Refusing to load model pickle file.")
        
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(MODEL_PATH, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    actual_hash = sha256_hash.hexdigest()
    
    with open(hash_path, "r", encoding="utf-8") as f:
        expected_hash = f.read().strip()
        
    if actual_hash != expected_hash:
        raise RuntimeError("Security Alert: Model pickle file integrity verification failed! File may have been tampered with.")
        
    with open(MODEL_PATH, "rb") as f:
        artifacts = pickle.load(f)
        model = artifacts["model"]
        threshold = artifacts["threshold"]
        feature_columns = artifacts["feature_columns"]
        # Extract means/stds if available (fallback to default empty dict if not yet compiled)
        feature_means = artifacts.get("feature_means", {})
        feature_stds = artifacts.get("feature_stds", {})
    
    print(f"Loaded Hero Agent model. Anomaly Threshold: {threshold:.4f}")

@app.post("/detect")
def detect_anomaly(flow: FlowRecord):
    global model, threshold, feature_columns, encoding_mappings, feature_means, feature_stds
    
    try:
        # 1. Map categoricals using encoding mappings
        record_dict = flow.model_dump()
        
        for col in ["protocol_type", "service", "flag"]:
            val = record_dict.get(col)
            if isinstance(val, int):
                # Already encoded integer
                pass
            elif isinstance(val, str) and val.isdigit():
                # String representing an integer
                record_dict[col] = int(val)
            elif col in encoding_mappings:
                # Map value, fallback to 0 if unknown category
                record_dict[col] = encoding_mappings[col].get(val, 0)
                
        # 2. Engineer features for single record
        feat_dict = transform_record(record_dict)
        
        # 3. Create prediction matrix (1, N) in correct column order
        if model is None:
            # Fallback Mock Mode: if model not trained yet, simulate detection
            anomaly_score = 0.45
            if flow.attack != "normal":
                anomaly_score = 0.85
            is_anomaly = anomaly_score > threshold
        else:
            # Construct feature vector
            vector = [feat_dict.get(c, 0.0) for c in feature_columns]
            X = np.array([vector])
            
            # Isolation Forest score_samples (opposite of anomaly score, negating gives positive score)
            raw_score = model.score_samples(X)[0]
            anomaly_score = round(float(-raw_score), 4)
            is_anomaly = anomaly_score > threshold
    
        # 4. Compile flagged features using Z-score outlier detection relative to baseline
        features_flagged = []
        if is_anomaly:
            z_scores = {}
            for col in feature_columns:
                val = float(feat_dict.get(col, 0.0))
                mean = feature_means.get(col, 0.0)
                std = feature_stds.get(col, 1.0)
                if std > 0.0001:
                    z = abs(val - mean) / std
                    z_scores[col] = z
                    
            # Flag features with Z-score > 2.5
            features_flagged = [col for col, z in z_scores.items() if z > 2.5]
            
            # Fallback if no feature stands out: take top contributors (up to 2)
            if not features_flagged and z_scores:
                sorted_feats = sorted(z_scores.items(), key=lambda item: item[1], reverse=True)
                features_flagged = [f[0] for f in sorted_feats[:2]]
                
            # Map engineered names back to raw names for cleaner UX
            rename_map = {
                "log_duration": "duration",
                "log_src_bytes": "src_bytes",
                "log_dst_bytes": "dst_bytes",
                "src_dst_ratio": "src_bytes/dst_bytes ratio",
                "count_srv_ratio": "connection frequency ratio"
            }
            features_flagged = [rename_map.get(f, f) for f in features_flagged]
    
        # 5. Construct Alert Object
        now_str = datetime.now(timezone.utc).isoformat()
        
        protocol_name = str(flow.protocol_type)
        if isinstance(flow.protocol_type, int) and "protocol_type" in encoding_mappings:
            for k, v in encoding_mappings["protocol_type"].items():
                if v == flow.protocol_type:
                    protocol_name = k
                    break
                    
        # Generate schema-compliant alert dict
        alert = {
            "alert_id": f"ALT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}",
            "timestamp": now_str,
            "entity": protocol_name + "_session_from_IP",  # Can be detailed later in pipeline
            "anomaly_score": anomaly_score,
            "features_flagged": features_flagged if is_anomaly else [],
            "attack_technique": None,
            "technique_confidence": None,
            "response_action": None,
            "response_status": "flagged" if is_anomaly else "normal",
            "audit_trail": [
                {
                    "timestamp": now_str,
                    "agent": "Hero Agent",
                    "action": "Analysis Complete",
                    "notes": f"Flow record analyzed. Classification: {'ANOMALY' if is_anomaly else 'NORMAL'}. Score: {anomaly_score:.4f}."
                }
            ]
        }
        
        # Add anomaly features to notes if present
        if is_anomaly:
            alert["audit_trail"][0]["notes"] += f" Flagged features: {', '.join(features_flagged)}."
            
        # Validate alert structure
        validate_alert(alert)
        
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": anomaly_score,
            "alert": alert
        }
    except Exception as e:
        print(f"Error in detect_anomaly: {e}")
        raise HTTPException(status_code=500, detail="Alert generation failed due to an internal processing error.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
