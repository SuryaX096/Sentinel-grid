import os
import sys
import json
import numpy as np

# Ensure workspace is on path
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from src.attribution_agent.feature_to_text import translate_features_to_description

# Define paths
CHROMA_STORE_DIR = os.path.join(WORKSPACE_DIR, "src", "attribution_agent", "chroma_store")
RESULTS_PATH = os.path.join(WORKSPACE_DIR, "evaluation", "results.md")

# 20 Hand-constructed benchmark test cases mapping anomalous feature patterns to expected MITRE techniques
TEST_CASES = [
    # DoS cases
    {"features": ["serror_rate", "count"], "expected_id": "T1498", "category": "DoS"},
    {"features": ["srv_serror_rate", "count"], "expected_id": "T1498", "category": "DoS"},
    {"features": ["serror_rate", "srv_serror_rate"], "expected_id": "T1498", "category": "DoS"},
    {"features": ["wrong_fragment"], "expected_id": "T1499", "category": "DoS"},
    {"features": ["wrong_fragment", "duration"], "expected_id": "T1499", "category": "DoS"},
    {"features": ["land"], "expected_id": "T1499", "category": "DoS"},
    
    # Discovery / Scanning cases
    {"features": ["diff_srv_rate", "dst_host_diff_srv_rate"], "expected_id": "T1046", "category": "Probe"},
    {"features": ["dst_host_diff_srv_rate"], "expected_id": "T1046", "category": "Probe"},
    {"features": ["srv_diff_host_rate"], "expected_id": "T1595", "category": "Probe"},
    {"features": ["dst_host_srv_diff_host_rate"], "expected_id": "T1595", "category": "Probe"},
    
    # R2L cases
    {"features": ["num_failed_logins", "count"], "expected_id": "T1110", "category": "R2L"},
    {"features": ["num_failed_logins", "logged_in"], "expected_id": "T1110", "category": "R2L"},
    {"features": ["num_failed_logins"], "expected_id": "T1110", "category": "R2L"},
    {"features": ["src_bytes", "duration"], "expected_id": "T1190", "category": "R2L"},
    {"features": ["dst_bytes", "duration"], "expected_id": "T1190", "category": "R2L"},
    {"features": ["logged_in", "duration", "service"], "expected_id": "T1133", "category": "R2L"},
    
    # U2R Privilege Escalation cases
    {"features": ["root_shell", "su_attempted"], "expected_id": "T1068", "category": "U2R"},
    {"features": ["root_shell", "num_compromised"], "expected_id": "T1068", "category": "U2R"},
    {"features": ["su_attempted", "num_access_files"], "expected_id": "T1548", "category": "U2R"},
    {"features": ["num_access_files", "num_shells"], "expected_id": "T1548", "category": "U2R"}
]

def run_evaluation():
    print("=" * 60)
    print("        ATTRIBUTION AGENT - BENCHMARK EVALUATION        ")
    print("=" * 60)
    
    if not os.path.exists(CHROMA_STORE_DIR):
        print(f"ERROR: ChromaDB store not found at {CHROMA_STORE_DIR}.")
        print("Please build the database index first:")
        print("python -m src.attribution_agent.build_mitre_index")
        return
        
    # Initialize connection to ChromaDB and loading sentence-transformers
    print("Connecting to local ChromaDB collection and loading embedder...")
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        chroma_client = chromadb.PersistentClient(path=CHROMA_STORE_DIR)
        collection = chroma_client.get_collection(name="mitre_techniques")
    except Exception as e:
        print(f"Failed to load dependencies or connect to vector DB: {e}")
        return
        
    print(f"ChromaDB ready. Executing {len(TEST_CASES)} evaluation cases...")
    
    correct = 0
    results = []
    
    for idx, case in enumerate(TEST_CASES):
        features = case["features"]
        expected_id = case["expected_id"]
        category = case["category"]
        
        # 1. Translate features to description
        desc = translate_features_to_description(features, 0.85)
        
        # 2. Query Vector DB
        query_vector = embedder.encode([desc])[0].tolist()
        res = collection.query(
            query_embeddings=[query_vector],
            n_results=1
        )
        
        predicted_id = "T0000"
        similarity = 0.0
        tech_name = "Unknown"
        
        if res and res["ids"] and res["ids"][0]:
            predicted_id = res["ids"][0][0]
            distance = res["distances"][0][0]
            similarity = max(0.0, 1.0 - (distance / 2.0))
            tech_name = res["metadatas"][0][0]["name"]
            
        is_correct = predicted_id == expected_id
        if is_correct:
            correct += 1
            
        results.append({
            "id": idx + 1,
            "features": ", ".join(features),
            "category": category,
            "expected": expected_id,
            "predicted": predicted_id,
            "predicted_name": tech_name,
            "similarity": similarity,
            "status": "PASS" if is_correct else "FAIL"
        })
        
        print(f"Case {idx+1:02d}: Ground Truth: {expected_id} | Predicted: {predicted_id} ({tech_name}) | Similarity: {similarity:.2%} | Status: {'PASS' if is_correct else 'FAIL'}")
        
    accuracy = correct / len(TEST_CASES)
    print(f"\nOverall Attribution Accuracy: {accuracy:.2%} ({correct}/{len(TEST_CASES)} correct)")
    
    # 3. Save to results.md
    print(f"Writing results to {RESULTS_PATH}...")
    
    # Compile markdown text
    results_md = f"""
## Attribution Agent Threat Classification Evaluation

**Date:** {pd_timestamp_now_str()}
**Attribution Mode:** Local Semantic Similarity Search (ChromaDB candidate retrieval)
**Embedding Model:** `all-MiniLM-L6-v2`
**Benchmark Size:** 20 Scenarios

### Performance Metrics Summary

*   **Overall Classification Accuracy:** `{accuracy:.2%}` ({correct} of {len(TEST_CASES)} cases matched correctly)
*   **Total Test Cases Evaluated:** `{len(TEST_CASES)}`

### Scenario Test Runs Breakdown

| ID | Flagged Features | Expected Technique ID | Predicted Technique ID | Predicted Technique Name | Similarity | Status |
|---|---|---|---|---|---|---|
"""
    
    for r in results:
        results_md += f"| {r['id']} | `{r['features']}` | **{r['expected']}** | **{r['predicted']}** | {r['predicted_name']} | `{r['similarity']:.2%}` | {'🟢 PASS' if r['status'] == 'PASS' else '🔴 FAIL'} |\n"
        
    # Read existing and append
    results_content = ""
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            results_content = f.read()
            
    # Check if section exists and replace, or append
    if "## Attribution Agent Threat Classification Evaluation" in results_content:
        parts = results_content.split("## Attribution Agent Threat Classification Evaluation")
        post_part = parts[1].split("## ")[1] if len(parts[1].split("## ")) > 1 else ""
        new_content = parts[0] + "## Attribution Agent Threat Classification Evaluation" + results_md + (f"\n## {post_part}" if post_part else "")
    else:
        new_content = results_content + "\n" + "## Attribution Agent Threat Classification Evaluation" + results_md
        
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Attribution evaluation output written successfully.")

def pd_timestamp_now_str():
    # Helper to print timestamp without pandas if not loaded yet
    try:
        import pandas as pd
        return pd.Timestamp.now().strftime('%Y-%m-%d')
    except Exception:
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')

if __name__ == "__main__":
    run_evaluation()
