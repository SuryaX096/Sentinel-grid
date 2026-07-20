import os
import pickle
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
from src.hero_agent.feature_engineering import engineer_features

# Define paths
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEST_HOLDOUT_PATH = os.path.join(WORKSPACE_DIR, "data", "processed", "test_holdout.csv")
MODEL_PATH = os.path.join(WORKSPACE_DIR, "src", "hero_agent", "model.pkl")
RESULTS_PATH = os.path.join(WORKSPACE_DIR, "evaluation", "results.md")

def evaluate_hero_agent():
    print("=" * 60)
    print("             HERO AGENT - QUANTITATIVE EVALUATION             ")
    print("=" * 60)
    
    # Check if artifacts exist
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Trained model not found at {MODEL_PATH}. Run training first.")
    if not os.path.exists(TEST_HOLDOUT_PATH):
        raise FileNotFoundError(f"Test holdout dataset not found at {TEST_HOLDOUT_PATH}. Run data prep first.")
    # Load model and metadata
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
        clf = artifacts["model"]
        threshold = artifacts["threshold"]
        feature_cols = artifacts["feature_columns"]
        
    print(f"Loaded model successfully. Detection Threshold: {threshold:.4f}")
    
    # Load test holdout dataset
    test_df = pd.read_csv(TEST_HOLDOUT_PATH)
    print(f"Loaded {len(test_df)} test holdout samples.")
    
    # Feature engineering
    test_df_engineered = engineer_features(test_df)
    
    X_test = test_df_engineered[feature_cols]
    y_test_true = (test_df["attack_category"] != "normal").astype(int).values
    
    # Predict scores (higher = more anomalous)
    raw_scores = clf.score_samples(X_test)
    y_test_scores = -raw_scores
    
    # Classification based on tuned threshold
    y_test_pred = (y_test_scores > threshold).astype(int)
    
    # Compute metrics
    precision, recall, f1, _ = precision_recall_fscore_support(y_test_true, y_test_pred, average="binary", zero_division=0)
    
    # Confusion matrix to calculate False Positive Rate (FPR)
    tn, fp, fn, tp = confusion_matrix(y_test_true, y_test_pred).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    
    # Metrics report
    print("\nQuantitative Evaluation Metrics (Holdout Set):")
    print(f"  - Precision:             {precision:.4f} ({precision:.2%})")
    print(f"  - Recall (Sensitivity):  {recall:.4f} ({recall:.2%})")
    print(f"  - F1-Score:              {f1:.4f}")
    print(f"  - False Positive Rate:   {fpr:.4f} ({fpr:.2%})")
    print(f"  - False Negative Rate:   {fnr:.4f} ({fnr:.2%})")
    print(f"  - True Negatives (TN):   {tn}")
    print(f"  - False Positives (FP):  {fp}")
    print(f"  - False Negatives (FN):  {fn}")
    print(f"  - True Positives (TP):   {tp}")
    
    print("\nClassification Report:")
    print(classification_report(y_test_true, y_test_pred, target_names=["Normal", "Anomaly"]))
    
    # Attack-category-wise performance
    print("\nDetection Rate by Attack Category:")
    categories = test_df["attack_category"].unique()
    for cat in categories:
        cat_mask = test_df["attack_category"] == cat
        cat_true = (test_df[cat_mask]["attack_category"] != "normal").astype(int).values
        # If it's normal, true labels are 0. Otherwise they are 1.
        cat_scores = y_test_scores[cat_mask]
        cat_pred = (cat_scores > threshold).astype(int)
        
        count = len(cat_pred)
        detected = np.sum(cat_pred == 1) if cat != "normal" else np.sum(cat_pred == 0)
        rate = detected / count if count > 0 else 0.0
        
        rate_label = "Clean Isolation Rate" if cat == "normal" else "Detection Rate"
        print(f"  - {cat.upper():<8} (N={count:<5}): {rate_label} = {rate:.2%}")
        
    # Write to results.md
    print(f"\nWriting results to {RESULTS_PATH}...")
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    
    # Read existing or start fresh
    results_content = ""
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            results_content = f.read()
            
    # Compile Hero evaluation section
    hero_md = f"""## Hero Agent Anomaly Detection Evaluation

**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d')}
**Model Type:** Isolation Forest (trained on normal traffic only)
**Tuned Score Threshold:** `{threshold:.4f}`

### Performance Summary Table

| Metric | Score (Value) | Percentage | Description |
|---|---|---|---|
| **Precision** | `{precision:.4f}` | {precision:.2%} | Proportion of flagged alerts that were actual attacks |
| **Recall (Sensitivity)** | `{recall:.4f}` | {recall:.2%} | Proportion of actual attacks successfully detected |
| **F1-Score** | `{f1:.4f}` | - | Harmonic mean of precision and recall |
| **False Positive Rate (FPR)** | `{fpr:.4f}` | {fpr:.2%} | Rate at which normal traffic is misidentified as anomalous |
| **False Negative Rate (FNR)** | `{fnr:.4f}` | {fnr:.2%} | Rate at which attacks slip through undetected |

### Confusion Matrix Counts

*   **True Negatives (TN):** `{tn}` (Normal traffic correctly identified)
*   **False Positives (FP):** `{fp}` (Normal traffic flagged as anomaly)
*   **False Negatives (FN):** `{fn}` (Attacks that went undetected)
*   **True Positives (TP):** `{tp}` (Attacks correctly flagged)

### Detection Breakdown by Attack Class

| Attack Class | Count (N) | Isolation/Detection Rate | Action Performance |
|---|---|---|---|
| **Normal (Inliers)** | {len(test_df[test_df["attack_category"] == "normal"])} | {np.sum(y_test_pred[test_df["attack_category"] == "normal"] == 0) / len(test_df[test_df["attack_category"] == "normal"]):.2%} | Clean Baseline Preservation |
| **DoS (Denial of Service)** | {len(test_df[test_df["attack_category"] == "DoS"])} | {np.sum(y_test_pred[test_df["attack_category"] == "DoS"] == 1) / len(test_df[test_df["attack_category"] == "DoS"]):.2%} | Volumetric Mitigation Triggered |
| **Probe (Scanning)** | {len(test_df[test_df["attack_category"] == "Probe"])} | {np.sum(y_test_pred[test_df["attack_category"] == "Probe"] == 1) / len(test_df[test_df["attack_category"] == "Probe"]):.2%} | Port/IP Scanning Throttling |
| **R2L (Unauthorized Access)** | {len(test_df[test_df["attack_category"] == "R2L"])} | {np.sum(y_test_pred[test_df["attack_category"] == "R2L"] == 1) / len(test_df[test_df["attack_category"] == "R2L"]):.2%} | Credential Abuse Blocking |
| **U2R (Privilege Escalation)** | {len(test_df[test_df["attack_category"] == "U2R"])} | {np.sum(y_test_pred[test_df["attack_category"] == "U2R"] == 1) / len(test_df[test_df["attack_category"] == "U2R"]):.2%} | Endpoint Isolation Escalation |

"""
    
    # Overwrite/Write results
    if "## Hero Agent Anomaly Detection Evaluation" in results_content:
        # Replace the section
        parts = results_content.split("## Hero Agent Anomaly Detection Evaluation")
        post_part = parts[1].split("## ")[1] if len(parts[1].split("## ")) > 1 else ""
        new_content = parts[0] + hero_md + (f"## {post_part}" if post_part else "")
    else:
        new_content = results_content + "\n" + hero_md
        
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Hero evaluation output written successfully.")

if __name__ == "__main__":
    evaluate_hero_agent()
