import os
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, precision_recall_fscore_support
from src.hero_agent.feature_engineering import engineer_features, get_final_feature_columns

# Define paths
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROCESSED_DATA_DIR = os.path.join(WORKSPACE_DIR, "data", "processed")
MODEL_PATH = os.path.join(WORKSPACE_DIR, "src", "hero_agent", "model.pkl")

def train_anomaly_detector():
    print("Loading processed training and validation data...")
    train_df = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "train.csv"))
    val_df = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "val.csv"))
    
    print("Engineering features...")
    train_df = engineer_features(train_df)
    val_df = engineer_features(val_df)
    
    feature_cols = get_final_feature_columns()
    print(f"Features selected for training ({len(feature_cols)}): {feature_cols}")
    
    # Isolation Forest is trained on 'normal' traffic to establish a clean baseline
    print("Filtering training dataset to include 'normal' traffic only for baseline learning...")
    train_normal = train_df[train_df["attack_category"] == "normal"]
    X_train = train_normal[feature_cols]
    
    print(f"Training Isolation Forest model on {len(X_train)} normal traffic samples...")
    # Set random state for reproducibility
    clf = IsolationForest(
        n_estimators=150, 
        max_samples="auto", 
        contamination=0.01, 
        random_state=42, 
        n_jobs=-1
    )
    clf.fit(X_train)
    
    print("Evaluating model and tuning detection threshold on validation set...")
    # Get features for validation
    X_val = val_df[feature_cols]
    # Ground truth: 1 for anomaly (any attack class), 0 for normal
    y_val_true = (val_df["attack_category"] != "normal").astype(int).values
    
    # Isolation Forest score_samples returns negative anomaly score (lower is more anomalous)
    # Let's convert it: higher value is more anomalous.
    # The score ranges typically from ~0.35 to ~0.8. Let's compute: 1.0 - score
    raw_scores = clf.score_samples(X_val)
    # Isolation Forest score_samples returns values in [-1, 0] or similar where values close to -1 are anomalies.
    # Specifically, it's defined as -1.0 * score_samples. Let's make it range from 0 to 1 where higher is anomalous.
    # Under sklearn, anomaly score = -clf.score_samples(X_val)
    # The paper's anomaly score is s(x, n) = 2^(- E(h(x)) / c(n)). It is in [0, 1].
    # In scikit-learn, score_samples returns the opposite of this anomaly score: -1 * score.
    # Therefore, we can get the standard [0, 1] anomaly score by negating score_samples.
    y_val_scores = -raw_scores
    
    # Grid search for the threshold that maximizes validation F1-score
    best_threshold = 0.5
    best_f1 = 0.0
    best_precision = 0.0
    best_recall = 0.0
    
    # We will search from 0.40 to 0.70
    thresholds = np.arange(0.40, 0.75, 0.01)
    for t in thresholds:
        y_val_pred = (y_val_scores > t).astype(int)
        precision, recall, f1, _ = precision_recall_fscore_support(y_val_true, y_val_pred, average="binary", zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = t
            best_precision = precision
            best_recall = recall
            
    print(f"Optimal Threshold Tuned: {best_threshold:.4f}")
    print(f"Validation Metrics at Threshold:")
    print(f"  - Precision: {best_precision:.4f}")
    print(f"  - Recall:    {best_recall:.4f}")
    print(f"  - F1-Score:  {best_f1:.4f}")
    
    # Print a detailed classification report at best threshold
    y_val_pred_best = (y_val_scores > best_threshold).astype(int)
    print("\nDetailed Validation Classification Report:")
    print(classification_report(y_val_true, y_val_pred_best, target_names=["Normal", "Anomaly"]))
    
    # Step 4: Save trained model, threshold, and feature columns list
    model_metadata = {
        "model": clf,
        "threshold": float(best_threshold),
        "feature_columns": feature_cols,
        "feature_means": X_train.mean().to_dict(),
        "feature_stds": X_train.std().to_dict()
    }
    
    print(f"Saving model artifacts to {MODEL_PATH}...")
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model_metadata, f)
        
    print("Training process completed.")

if __name__ == "__main__":
    train_anomaly_detector()
