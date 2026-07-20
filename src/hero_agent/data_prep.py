import os
import urllib.request
import json
import pandas as pd
from sklearn.model_selection import train_test_split

# Define paths
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DATA_DIR = os.path.join(WORKSPACE_DIR, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(WORKSPACE_DIR, "data", "processed")
HERO_AGENT_DIR = os.path.join(WORKSPACE_DIR, "src", "hero_agent")

TRAIN_URL = "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTrain+.txt"
TEST_URL = "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTest+.txt"

COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes", 
    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in", 
    "num_compromised", "root_shell", "su_attempted", "num_root", "num_file_creations", 
    "num_shells", "num_access_files", "num_outbound_cmds", "is_host_login", 
    "is_guest_login", "count", "srv_count", "serror_rate", "srv_serror_rate", 
    "rerror_rate", "srv_rerror_rate", "same_srv_rate", "diff_srv_rate", 
    "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count", 
    "dst_host_same_srv_rate", "dst_host_diff_srv_rate", "dst_host_same_src_port_rate", 
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate", "dst_host_srv_serror_rate", 
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate", "attack", "last_flag"
]

# Attack mapping from fine-grained attack classes to 4 broad categories plus normal
ATTACK_MAPPING = {
    # DoS
    "back": "DoS", "land": "DoS", "neptune": "DoS", "pod": "DoS", "smurf": "DoS", "teardrop": "DoS",
    "apache2": "DoS", "mailbomb": "DoS", "processtable": "DoS", "udpstorm": "DoS",
    # Probe
    "ipsweep": "Probe", "nmap": "Probe", "portsweep": "Probe", "satan": "Probe",
    "mscan": "Probe", "saint": "Probe",
    # R2L
    "ftp_write": "R2L", "guess_passwd": "R2L", "imap": "R2L", "multihop": "R2L", "phf": "R2L",
    "spy": "R2L", "warezclient": "R2L", "warezmaster": "R2L", "sendmail": "R2L", "named": "R2L",
    "xlock": "R2L", "xsnoop": "R2L", "snmpgetattack": "R2L", "snmpguess": "R2L", "httptunnel": "R2L",
    "worm": "R2L",
    # U2R
    "buffer_overflow": "U2R", "loadmodule": "U2R", "perl": "U2R", "ps": "U2R", "rootkit": "U2R",
    "sqlattack": "U2R", "xterm": "U2R",
    # Normal
    "normal": "normal"
}

def download_file(url: str, dest_path: str):
    """
    Downloads a file from a URL to a local destination path.
    """
    if os.path.exists(dest_path):
        print(f"File already exists: {dest_path}")
        return
    print(f"Downloading {url} to {dest_path}...")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    # Use standard library urllib
    urllib.request.urlretrieve(url, dest_path)
    print("Download completed successfully.")

def prep_data():
    """
    Downloads, processes, encodes, and splits the NSL-KDD dataset.
    """
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    train_raw_path = os.path.join(RAW_DATA_DIR, "KDDTrain+.txt")
    test_raw_path = os.path.join(RAW_DATA_DIR, "KDDTest+.txt")
    
    # Step 1: Download datasets
    download_file(TRAIN_URL, train_raw_path)
    download_file(TEST_URL, test_raw_path)
    
    # Step 2: Load into DataFrames
    print("Loading datasets...")
    train_df = pd.read_csv(train_raw_path, header=None, names=COLUMNS)
    test_df = pd.read_csv(test_raw_path, header=None, names=COLUMNS)
    
    # Step 3: Process labels and map attack types
    print("Processing attack mappings...")
    # Standardize spaces
    train_df["attack"] = train_df["attack"].astype(str).str.strip()
    test_df["attack"] = test_df["attack"].astype(str).str.strip()
    
    train_df["attack_category"] = train_df["attack"].map(lambda x: ATTACK_MAPPING.get(x, "R2L"))
    test_df["attack_category"] = test_df["attack"].map(lambda x: ATTACK_MAPPING.get(x, "R2L"))
    
    # Step 4: Encode categorical fields
    print("Encoding categorical fields...")
    categorical_cols = ["protocol_type", "service", "flag"]
    encoding_mappings = {}
    
    for col in categorical_cols:
        # Merge training and testing values to ensure complete coverage of categorical labels
        unique_vals = sorted(list(set(train_df[col].unique()) | set(test_df[col].unique())))
        mapping = {val: idx for idx, val in enumerate(unique_vals)}
        encoding_mappings[col] = mapping
        
        # Apply encoding
        train_df[col] = train_df[col].map(mapping)
        test_df[col] = test_df[col].map(mapping)
        
    # Save encoding mappings for the detect API
    metadata_path = os.path.join(HERO_AGENT_DIR, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump({
            "encoding_mappings": encoding_mappings,
            "categorical_cols": categorical_cols,
            "attack_mapping": ATTACK_MAPPING
        }, f, indent=4)
    print(f"Saved encoding metadata to {metadata_path}")
    
    # Step 5: Save processed test holdout
    test_holdout_path = os.path.join(PROCESSED_DATA_DIR, "test_holdout.csv")
    test_df.to_csv(test_holdout_path, index=False)
    print(f"Saved test holdout to {test_holdout_path} ({len(test_df)} rows)")
    
    # Step 6: Split train_df into train and validation sets (80/20)
    print("Splitting train and validation sets...")
    train_split, val_split = train_test_split(train_df, test_size=0.2, random_state=42, stratify=train_df["attack_category"])
    
    train_processed_path = os.path.join(PROCESSED_DATA_DIR, "train.csv")
    val_processed_path = os.path.join(PROCESSED_DATA_DIR, "val.csv")
    
    train_split.to_csv(train_processed_path, index=False)
    val_split.to_csv(val_processed_path, index=False)
    
    print(f"Saved train dataset to {train_processed_path} ({len(train_split)} rows)")
    print(f"Saved validation dataset to {val_processed_path} ({len(val_split)} rows)")
    print("Data preparation complete.")

if __name__ == "__main__":
    prep_data()
