import numpy as np
import pandas as pd

# Standard features we want to use for model training (numerical features + our encoded categories)
FEATURE_COLS = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes", 
    "wrong_fragment", "hot", "num_failed_logins", "logged_in", "count", "srv_count", 
    "serror_rate", "srv_serror_rate", "rerror_rate", "srv_rerror_rate", 
    "same_srv_rate", "diff_srv_rate", "srv_diff_host_rate", "dst_host_count", 
    "dst_host_srv_count", "dst_host_same_srv_rate", "dst_host_diff_srv_rate", 
    "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate", 
    "dst_host_serror_rate", "dst_host_srv_serror_rate", 
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate"
]

def transform_record(record: dict) -> dict:
    """
    Transforms a single flow log dictionary by engineering features.
    Ensures that values are appropriately scaled and interaction features are created.
    """
    # Create a copy to prevent mutation
    feat = record.copy()
    
    # 1. Log transformations for highly skewed distributions
    feat["log_duration"] = np.log1p(float(feat.get("duration", 0)))
    feat["log_src_bytes"] = np.log1p(float(feat.get("src_bytes", 0)))
    feat["log_dst_bytes"] = np.log1p(float(feat.get("dst_bytes", 0)))
    
    # 2. Ratio metrics (with smoothing to prevent division by zero)
    src_bytes = float(feat.get("src_bytes", 0))
    dst_bytes = float(feat.get("dst_bytes", 0))
    feat["src_dst_ratio"] = src_bytes / (dst_bytes + 1.0)
    
    count = float(feat.get("count", 0))
    srv_count = float(feat.get("srv_count", 0))
    feat["count_srv_ratio"] = count / (srv_count + 1.0)
    
    return feat

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies feature engineering transformations to a Pandas DataFrame.
    """
    df_out = df.copy()
    
    # 1. Log transforms
    df_out["log_duration"] = np.log1p(df_out["duration"].astype(float))
    df_out["log_src_bytes"] = np.log1p(df_out["src_bytes"].astype(float))
    df_out["log_dst_bytes"] = np.log1p(df_out["dst_bytes"].astype(float))
    
    # 2. Ratios
    df_out["src_dst_ratio"] = df_out["src_bytes"].astype(float) / (df_out["dst_bytes"].astype(float) + 1.0)
    df_out["count_srv_ratio"] = df_out["count"].astype(float) / (df_out["srv_count"].astype(float) + 1.0)
    
    return df_out

def get_final_feature_columns() -> list:
    """
    Returns the list of final feature column names that should be fed into the model.
    """
    # Exclude raw duration, src_bytes, dst_bytes, count and replace with engineered ones
    base_cols = [c for c in FEATURE_COLS if c not in ["duration", "src_bytes", "dst_bytes", "count"]]
    engineered_cols = ["log_duration", "log_src_bytes", "log_dst_bytes", "src_dst_ratio", "count_srv_ratio"]
    return base_cols + engineered_cols
