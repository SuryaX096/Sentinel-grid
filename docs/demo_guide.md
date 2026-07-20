# SentinelMind AI — Hackathon Demo Guide & Playbook

This document prepares you to present a flawless, high-impact demonstration of the SentinelMind AI platform to hackathon judges. It includes startup sequences, checklist flows, backup/offline procedures, talking points, and answers to common technical questions.

---

## 1. Best Startup Command Sequence

To ensure the microservices initialize in correct order and establish clean network communication, execute the following commands in separate terminals:

```bash
# 1. Activate your virtual environment in each terminal session:
# On Windows: .venv\Scripts\Activate.ps1
# On macOS/Linux: source .venv/bin/activate

# 2. Terminal 1: Launch Hero Agent Anomaly Detector (Port 8001)
python -m src.hero_agent.detect_api
# Wait 3 seconds for model load message: "Loaded Hero Agent model."

# 3. Terminal 2: Launch Attribution Agent Threat Classifier (Port 8002)
python -m src.attribution_agent.attribute_api
# Wait 3 seconds for ChromaDB message: "Connected to local ChromaDB collection..."

# 4. Terminal 3: Launch Supporting Agent Incident Orchestrator (Port 8003)
python -m src.supporting_agent.respond_api
# Wait 2 seconds for message: "FastAPI - Uvicorn running..."

# 5. Terminal 4: Launch SOC Console Dashboard (Port 8501)
streamlit run src/dashboard/app.py
# Your browser will open the tab at http://localhost:8501

# 6. Terminal 5: Traffic Replay Simulator (Ready to trigger during demo)
# Run when ready to show live ingestion:
python -m src.integration.replay_demo --count 15 --interval 1.5
```

---

## 2. 3-Minute & 5-Minute Demo Checklist

### 3-Minute Lightning Pitch Flow
*   **0:00 - 0:45 (The Hook & Idle Console):** Show the clean dark-themed dashboard. Explain the problem (rule-based tools miss zero-days, analysts suffer alert fatigue). Highlight that the SOC feed is currently idle.
*   **0:45 - 1:45 (Live Ingestion & Anomaly Detection):** Trigger the `replay_demo.py` script. Point out the immediate update of the dashboard metrics (Gradients and hover states). Show how the **Hero Agent** is extracting outlier features (Z-scores) in real-time.
*   **1:45 - 2:30 (Semantic Attribution & Response):** Navigate to the **Gated Approval Terminal** on the right. Show a pending alert (e.g. `isolate_endpoint` on a database server). Explain that **Attribution Agent** mapped this to a specific MITRE ATT&CK technique, and **Supporting Agent** prioritized it based on asset value and active CVEs.
*   **2:30 - 3:00 (Human-in-the-Loop Containment):** Approve the isolation playbook. Show the status update instantly change to `executed` and the audit log append the analyst name and rationale. Wrap up with the core value: "Proactive, context-aware containment in seconds."

### 5-Minute Deep-Dive Pitch Flow
*   **Add (0:00 - 1:00):** Show the **ChromaDB Threat Intelligence (MITRE)** tab. Explain how local vector similarity embeds and maps raw network parameters to standard adversary techniques.
*   **Add (4:00 - 5:00):** Show the quantitative model evaluation numbers (`evaluation/results.md`). Prove that your platform isn't just a mock UI, but a statistically validated detector yielding **95.8% precision** on holdout splits.

---

## 3. Backup & Offline Demo Plans

### Offline Demo Plan (No Internet Access)
- **Local Vectors:** The Attribution Agent automatically operates locally using persistent sentence embeddings in `src/attribution_agent/chroma_store` instead of calling external LLMs.
- **Offline Assets:** The dashboard shield logo utilizes standard CSS emojis rather than external URLs.
- **Verification:** Turn off Wi-Fi and verify the servers load and replay traffic locally.

### Backup Demo Plan (APIs/Databases Fail to Start)
If local FastAPI services fail or security software blocks port connections during the demo, use the pre-built **Mock Alert Generator** to populate the dashboard instantly:
```bash
# Populate alerts.db with 15 realistic security incident records
python -c "from src.common.mock_alert_generator import generate_single_mock_alert; import sqlite3, json; conn=sqlite3.connect('alerts.db'); cursor=conn.cursor(); cursor.execute('DELETE FROM alerts'); [conn.execute('INSERT OR REPLACE INTO alerts VALUES (?,?,?,?,?,?,?,?,?,?)', (a:='ALT-'+str(i), '2026-07-20T10:00:00Z', 'database-server', 0.85, '[\"serror_rate\"]', 'T1498: Denial of Service', 0.88, 'isolate_endpoint', 'pending_approval', '[]')) for i in range(15)]; conn.commit(); conn.close(); print('Database populated with backup alerts!')"
```
Refresh the Streamlit dashboard to show the populated mock SOC feed instantly.

---

## 4. Key Judge Talking Points

*   **"Semi-Supervised" Advantage:** We don't train our model on labeled attack signatures (which change daily). We train on *normal behavior*. Anything else is anomalous, making it native to zero-day identification.
*   **Natural Language Bridge:** We solve the "So What?" of ML alerts. Translating connection statistics into prose descriptions allows ChromaDB vector similarity to map anomalies directly to MITRE ATT&CK concepts.
*   **Gated Blast-Radius Containment:** Full automation is dangerous. SentinelMind AI enforces automated execution only for low-impact containment (like snapshotting VMs) while gating high-impact containment (like blocking database IPs) behind human-in-the-loop approvals.
*   **Audit-Trail Compliance:** Every action taken by any agent is logged in an immutable-style audit trail, critical for regulatory SOC audits.

---

## 5. Common Judge Questions & Answers

*   **Q1: How does your Isolation Forest model handle concept drift?**
    *   *A:* In production, connection behaviors change over time. SentinelMind AI is structured to run daily retrains on verified normal flows, updating `model.pkl` and its SHA-256 integrity hash programmatically without interrupting API services.
*   **Q2: Microservice calls add communication latency. How do you scale this?**
    *   *A:* While localhost FastAPI REST is excellent for microservice decoupling in a prototype, a production enterprise pipeline would combine these agent scripts inside an asynchronous worker consumer listening to a distributed broker like Apache Kafka.
*   **Q3: Why did you use the NSL-KDD dataset? It is old.**
    *   *A:* NSL-KDD is a cleaned benchmark version of the standard KDD'99 dataset, widely used to validate ML-based intrusion detection systems. For enterprise deployment, we would train the Isolation Forest model on raw NetFlow / IPFIX traffic captures unique to the client's network.

---

## 6. Performance Metrics Summary

To show judges you have validated your work, quote these numbers from your test evaluation suites:
*   **Hero Agent (ML anomaly detection):**
    *   **Precision:** `95.8%` (High precision means minimal false alarms for SOC analysts).
    *   **Recall:** `84.3%` (Identifies the vast majority of network anomalies).
*   **Attribution Agent (ChromaDB Vector Matching):**
    *   **Accuracy:** `65.0%` (Successful classification across 20 distinct scenario scripts mapping to the catalog of core MITRE threat vectors).
