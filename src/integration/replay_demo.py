import os
import time
import numpy as np
import pandas as pd
from src.integration.pipeline import process_flow_record

# Define paths
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEST_HOLDOUT_PATH = os.path.join(WORKSPACE_DIR, "data", "processed", "test_holdout.csv")

def run_replay(interval_sec: float = 1.5, max_records: int = 50):
    """
    Replays flow records from the holdout dataset and feeds them into the pipeline.
    """
    print("=" * 60)
    print("      CYBER RESILIENCE PLATFORM - TRAFFIC REPLAY SIMULATOR      ")
    print("=" * 60)
    
    if not os.path.exists(TEST_HOLDOUT_PATH):
        print(f"ERROR: Holdout dataset not found at {TEST_HOLDOUT_PATH}.")
        print("Please run the data preparation script first: ")
        print("python -m src.hero_agent.data_prep")
        return
        
    print(f"Loading holdout records from {TEST_HOLDOUT_PATH}...")
    df = pd.read_csv(TEST_HOLDOUT_PATH)
    print(f"Loaded {len(df)} records.")
    
    # Stratify and sample to get a good mix of normal and attack types for demonstration
    normal_samples = df[df["attack_category"] == "normal"]
    attack_samples = df[df["attack_category"] != "normal"]
    
    print(f"Available: Normal={len(normal_samples)}, Attacks/Anomalies={len(attack_samples)}")
    
    # We want a clean stream containing normal connections with periodic anomalies
    # Let's construct a sample list of normal records and attack records safely
    num_attacks = min(10, len(attack_samples))
    if max_records < num_attacks:
        num_attacks = max_records
    num_normals = max(0, min(max_records - num_attacks, len(normal_samples)))
    num_attacks = max_records - num_normals
    
    sampled_normal = normal_samples.sample(n=num_normals, random_state=42) if num_normals > 0 else pd.DataFrame()
    sampled_attack = attack_samples.sample(n=num_attacks, random_state=42) if num_attacks > 0 else pd.DataFrame()
    
    # Interleave them so anomalies appear periodically (every 4-5 packets)
    demo_df = pd.concat([sampled_normal, sampled_attack]).sample(frac=1.0, random_state=10).reset_index(drop=True)
    
    print(f"Starting traffic replay of {len(demo_df)} records (interval: {interval_sec}s)...")
    print("Press Ctrl+C to stop.\n")
    
    # Standard flow record columns expected by detect_api
    flow_fields = [
        "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes", 
        "land", "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in", 
        "num_compromised", "root_shell", "su_attempted", "num_root", "num_file_creations", 
        "num_shells", "num_access_files", "num_outbound_cmds", "is_host_login", 
        "is_guest_login", "count", "srv_count", "serror_rate", "srv_serror_rate", 
        "rerror_rate", "srv_rerror_rate", "same_srv_rate", "diff_srv_rate", 
        "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count", 
        "dst_host_same_srv_rate", "dst_host_diff_srv_rate", "dst_host_same_src_port_rate", 
        "dst_host_srv_diff_host_rate", "dst_host_serror_rate", "dst_host_srv_serror_rate", 
        "dst_host_rerror_rate", "dst_host_srv_rerror_rate", "attack"
    ]
    
    for idx, row in demo_df.iterrows():
        # Build dictionary
        flow_record = {}
        for field in flow_fields:
            val = row[field]
            # Convert numpy types to native Python types for JSON serialization
            if isinstance(val, (np.integer,)):
                flow_record[field] = int(val)
            elif isinstance(val, (np.floating,)):
                flow_record[field] = float(val)
            else:
                flow_record[field] = str(val) if not isinstance(val, (int, float, str)) else val
                
        # Send through agent pipeline
        t0 = time.time()
        alert = process_flow_record(flow_record)
        t_elapsed = time.time() - t0
        
        # Display summary in console
        alert_id = alert["alert_id"]
        status = alert["response_status"]
        score = alert["anomaly_score"]
        entity = alert["entity"]
        attack_cat = row["attack_category"]
        
        indicator = "[NORMAL]"
        if status in ["executed", "pending_approval"]:
            indicator = "[ANOMALY]" if score > 0.8 else "[SUSPICIOUS]"
        elif status == "pipeline_error":
            indicator = "[PIPELINE ERROR]"
            
        print(f"[{idx+1:02d}/{len(demo_df):02d}] {indicator} ID: {alert_id} | Score: {score:.3f}")
        print(f"      Entity: {entity} | Ground Truth: {attack_cat.upper()}")
        
        if status in ["executed", "pending_approval"]:
            print(f"      Attribution: {alert.get('attack_technique')}")
            print(f"      Response Action: {alert.get('response_action')} (Status: {status})")
            flagged = alert.get("features_flagged", [])
            if flagged:
                print(f"      Flagged features: {', '.join(flagged)}")
                
        print(f"      Pipeline execution time: {t_elapsed:.3f}s")
        print("-" * 60)
        
        time.sleep(interval_sec)
        
    print("Replay simulation completed.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Replay NSL-KDD network flow records.")
    parser.add_argument("--interval", type=float, default=1.5, help="Interval in seconds between flows.")
    parser.add_argument("--count", type=int, default=30, help="Total number of records to replay.")
    args = parser.parse_args()
    
    try:
        run_replay(interval_sec=args.interval, max_records=args.count)
    except KeyboardInterrupt:
        print("\nReplay stopped by user.")
