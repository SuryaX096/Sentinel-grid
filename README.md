# SentinelGrid — Cyber Resilience Platform
### Autonomous Multi-Agent Threat Detection, Semantic ATT&CK Attribution, and Gated Incident Response
**ET AI Hackathon 2026 — Problem Statement 7 Submission**

---

## 1. Project Overview

Enterprise digital infrastructures are subject to increasingly complex, high-velocity cybersecurity threats. Traditional security systems rely heavily on static, rule-based matching (like signature detection), which fails to identify novel zero-day exploits. Once an anomaly is detected, Security Operations Center (SOC) analysts are often overwhelmed by alerts that lack semantic context (e.g., matching the anomaly to specific threat tactics) and do not trigger immediate coordinated response actions.

**SentinelMind AI** is an agentic cyber resilience platform designed to autonomously defend enterprise networks. Using a three-tier collaborative agent system, it ingests raw network connection flows, classifies anomalies using machine learning, attributes them semantically to known MITRE ATT&CK techniques, prioritizes response playbooks based on target asset values/CVEs, and enforces gated human-in-the-loop approvals for high-impact containment actions.

---

## 2. Platform Architecture

The platform operates on a microservice architecture consisting of three FastAPI agent services, a shared SQLite database store, and an interactive Streamlit SOC console.

```mermaid
graph TD
    %% Data Ingestion
    A[Raw Network Flow Log / Replay] -->|Inference request| B(Hero Agent: detect_api)
    
    %% Hero Agent (ML Detection)
    subgraph Hero Agent - Anomaly Detection (:8001)
        B --> C{Isolation Forest Model}
        C -->|Inlier / Normal| D[Log Connection & Resolve]
        C -->|Anomaly detected| E[Calculate Z-Scores & Flag Features]
    end
    
    %% Attribution Agent (Threat Intel)
    E -->|JSON Alert Payload| F(Attribution Agent: attribute_api)
    subgraph Attribution Agent - Threat Intel (:8002)
        F --> G[feature_to_text: Translate features to sentence]
        G --> H[ChromaDB persistent vector search]
        H --> I{Gemini API configured?}
        I -->|Yes| J[Gemini 1.5 Flash: CTI LLM Validation]
        I -->|No| K[Local Semantic Similarity Top Candidate]
        J --> L[Enrich Alert with ATT&CK Technique & Details]
        K --> L
    end
    
    %% Supporting Agent (Mitigation)
    L -->|Enriched Alert| M(Supporting Agent: respond_api)
    subgraph Supporting Agent - Orchestrator (:8003)
        M --> N[Load asset_inventory.json & CVE profiles]
        N --> O[Select playbook_config.json action by risk score]
        O --> P{High Blast Radius / Auto-Execute?}
        P -->|Low / Auto-Execute: true| Q[Update Status: executed]
        P -->|High / Auto-Execute: false| R[Update Status: pending_approval]
    end
    
    %% Operations Dashboard & SQLite DB
    Q --> S[(SQLite alerts.db)]
    R --> S
    D --> S
    
    S --> T[Streamlit Dashboard SOC Console :8501]
    T -->|Interactive Manual Approval / Override| U[Call approve_api]
    U -->|Action executed/dismissed| S
```

### Alert Data Schema
Every alert passing through the agent pipeline is strictly validated against a unified JSON schema containing the following required keys:
*   `alert_id`: Unique identifier (UUID-based).
*   `timestamp`: ISO-8601 UTC timestamp.
*   `entity`: Target entity name (e.g. protocol or IP session).
*   `anomaly_score`: Float value between `0.0` and `1.0` representing ML detection confidence.
*   `features_flagged`: List of outlier connection metrics triggering the alert.
*   `attack_technique`: Mapped MITRE ATT&CK technique name and ID.
*   `technique_confidence`: Float value between `0.0` and `1.0` representing semantic search/LLM confidence.
*   `response_action`: Planned mitigation playbook action.
*   `response_status`: Current state (`normal`, `resolved`, `executed`, `pending_approval`, `pipeline_error`, `dismissed`).
*   `audit_trail`: Sequential array of agent actions and timestamps.

---

## 3. Platform Features

*   **Semi-Supervised ML Anomaly Detection:** Hero Agent establishes a normal network traffic baseline using an `IsolationForest` model. Unseen traffic is scored, and feature outliers are dynamically flagged using statistical Z-score thresholds relative to the baseline.
*   **Dual-Mode Semantic Threat Attribution:** Attribution Agent translates abstract flagged features (e.g., `serror_rate`, `dst_host_diff_srv_rate`) into natural-language threat behavior. It queries a persistent vector database (ChromaDB) for candidate MITRE ATT&CK mappings. If a `GEMINI_API_KEY` is present, it validates findings using Google's Gemini 1.5 Flash LLM; otherwise, it falls back to local vector similarity metrics.
*   **Context-Aware Risk Prioritization:** Supporting Agent scores threats using an integrated calculation combining the model's anomaly score, the asset's criticality weight (low, medium, high, critical), and a boost factor if the target asset has active known CVEs.
*   **Gated Human-in-the-Loop Consoles:** High blast-radius response actions (e.g., `isolate_endpoint`, `revoke_session`) pause in `pending_approval` state, highlighting a red pulsing alert banner on the dashboard for analyst intervention.
*   **Comprehensive Audit Logs:** An append-only audit trail records the timeline and reasoning of each agent's decisions, ensuring compliance and transparency.

---

## 4. Installation & Virtual Environment Setup

### 4.1 Creating the Virtual Environment
To isolate the project dependencies and prevent library mismatches, set up a Python virtual environment:

```bash
# 1. Clone the repository
git clone https://github.com/SuryaX096/Cyber-resilience.git
cd Cyber-resilience

# 2. Create a virtual environment (Python 3.9+ recommended)
python -m venv .venv

# 3. Activate the virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (Command Prompt):
.venv\Scripts\activate.bat
# On macOS / Linux:
source .venv/bin/activate
```

### 4.2 Installing Dependencies
Install the pinned dependencies (including scikit-learn, streamlit, fastapi, chromadb, sentence-transformers, and streamlit-autorefresh):
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
*Note: The `sentence-transformers` library automatically installs PyTorch, which may require a download of up to 2GB depending on your platform.*

---

## 5. Environment Variables Configuration

The platform can run out-of-the-box using default localhost configurations. To enable high-fidelity LLM validation and custom settings, copy the `.env.example` file to `.env` and configure:

```bash
cp .env.example .env
```

### Configuration Parameters
| Parameter | Default | Purpose |
|-----------|---------|---------|
| `GEMINI_API_KEY` | None | API key from Google AI Studio. Enables LLM threat validation mode. |
| `HERO_AGENT_PORT` | `8001` | FastAPI port for Hero Agent Anomaly Detector. |
| `ATTRIBUTION_AGENT_PORT` | `8002` | FastAPI port for Attribution Agent Threat Classifier. |
| `SUPPORTING_AGENT_PORT` | `8003` | FastAPI port for Supporting Agent Response engine. |
| `DB_PATH` | `alerts.db` | SQLite database file location. |

---

## 6. Running the Project

Follow these steps sequentially to prepare, build, and run the multi-agent platform.

### Step 1: Pre-process Dataset & Train the ML Model
Run the data preparation pipeline to download the NSL-KDD dataset, map attack categories, encode fields, and train the Isolation Forest model (calculates a SHA-256 integrity checksum on save):
```bash
# Download and split NSL-KDD
python -m src.hero_agent.data_prep

# Train model and generate checksum
python -m src.hero_agent.train_model
```

### Step 2: Build the MITRE ATT&CK Semantic Index
Embed the curated threat technique catalog into the persistent ChromaDB local database using sentence embeddings:
```bash
python -m src.attribution_agent.build_mitre_index
```

### Step 3: Start the Agent Microservices
Run the three FastAPI agent servers in separate terminals (ensure your virtual environment is active in each):

```bash
# Terminal 1: Hero Agent Anomaly Detector (Runs on Port 8001)
python -m src.hero_agent.detect_api

# Terminal 2: Attribution Agent Threat Classifier (Runs on Port 8002)
python -m src.attribution_agent.attribute_api

# Terminal 3: Supporting Agent Response Engine (Runs on Port 8003)
python -m src.supporting_agent.respond_api
```

### Step 4: Launch the SOC Console Dashboard
Launch the Streamlit analytics interface:
```bash
streamlit run src/dashboard/app.py
```
*The dashboard will be active in your browser at `http://localhost:8501`.*

### Step 5: Start the Traffic Replay Simulator
In another terminal session, stream network flows into the pipeline to simulate real-time traffic:
```bash
# Streams 30 connections with a 1.5s interval
python -m src.integration.replay_demo --count 30 --interval 1.5
```

---

## 7. API Reference & Schemas

### 7.1 Hero Agent (`/detect`)
*   **Path:** `POST http://127.0.0.1:8001/detect`
*   **Payload Example:**
    ```json
    {
      "duration": 0.0, "protocol_type": "tcp", "service": "http", "flag": "SF",
      "src_bytes": 215.0, "dst_bytes": 4507.0, "land": 0, "wrong_fragment": 0,
      "urgent": 0, "hot": 0, "num_failed_logins": 0, "logged_in": 1,
      "num_compromised": 0, "root_shell": 0, "su_attempted": 0, "num_root": 0,
      "num_file_creations": 0, "num_shells": 0, "num_access_files": 0,
      "num_outbound_cmds": 0, "is_host_login": 0, "is_guest_login": 0,
      "count": 1.0, "srv_count": 1.0, "serror_rate": 0.0, "srv_serror_rate": 0.0,
      "rerror_rate": 0.0, "srv_rerror_rate": 0.0, "same_srv_rate": 1.0,
      "diff_srv_rate": 0.0, "srv_diff_host_rate": 0.0, "dst_host_count": 1.0,
      "dst_host_srv_count": 1.0, "dst_host_same_srv_rate": 1.0,
      "dst_host_diff_srv_rate": 0.0, "dst_host_same_src_port_rate": 1.0,
      "dst_host_srv_diff_host_rate": 0.0, "dst_host_serror_rate": 0.0,
      "dst_host_srv_serror_rate": 0.0, "dst_host_rerror_rate": 0.0,
      "dst_host_srv_rerror_rate": 0.0, "attack": "normal"
    }
    ```
*   **Response Sample:**
    ```json
    {
      "is_anomaly": false,
      "anomaly_score": 0.3821,
      "alert": {
        "alert_id": "ALT-20260720-c48f219d",
        "timestamp": "2026-07-20T10:15:30.450123",
        "entity": "tcp_session_from_IP",
        "anomaly_score": 0.3821,
        "features_flagged": [],
        "attack_technique": null,
        "technique_confidence": null,
        "response_action": null,
        "response_status": "normal",
        "audit_trail": [
          {
            "timestamp": "2026-07-20T10:15:30.450123",
            "agent": "Hero Agent",
            "action": "Analysis Complete",
            "notes": "Flow record analyzed. Classification: NORMAL. Score: 0.3821."
          }
        ]
      }
    }
    ```

### 7.2 Attribution Agent (`/attribute`)
*   **Path:** `POST http://127.0.0.1:8002/attribute`
*   **Description:** Translates flagged features to descriptive prose and queries ChromaDB vectors. Returns the enriched alert object.

### 7.3 Supporting Agent (`/respond`)
*   **Path:** `POST http://127.0.0.1:8003/respond`
*   **Description:** Orchestrates the risk mitigation playbook based on asset value and CVE profile.

### 7.4 Supporting Agent Approval Gate (`/approve`)
*   **Path:** `POST http://127.0.0.1:8003/approve`
*   **Payload Example:**
    ```json
    {
      "alert": { ... },
      "approved": true,
      "analyst_name": "SOC Manager",
      "notes": "Containment playbook authorized."
    }
    ```

---

## 8. Verification & Test Execution

The test suite validates integration behavior and JSON schema compliance. To execute tests:
```bash
python -m unittest tests/test_pipeline.py
```

To view trained model precision and recall figures on the test holdout split:
```bash
python -m evaluation.evaluate_hero
python -m evaluation.evaluate_attribution
```
*Results are appended and formatted within `evaluation/results.md`.*

---

## 9. Dashboard Screenshot Placeholders

The dark-themed dashboard provides a complete overview of the platform status.
*   **Dashboard Alerts Console:** `[Placeholder: docs/screenshots/dashboard_live_alerts.png]`
*   **Pending SOC Approvals Banner:** `[Placeholder: docs/screenshots/dashboard_pending_approvals.png]`
*   **MITRE ATT&CK Semantic Sandbox:** `[Placeholder: docs/screenshots/dashboard_threat_intel.png]`

---

## 10. Troubleshooting & FAQ

*   **Q: ImportError: DLL load failed while importing _argkmin_classmode**
    *   *A:* Your operating system has active Application Control Policies (e.g. WDAC or AppLocker) blocking Python from loading scikit-learn's native compiled C++ DLLs from user directory paths. Ensure Python is allowed in your OS policies, or use the pre-built `model.pkl` along with its integrity file `model.pkl.sha256` which are checked into the repository, skipping the local `train_model.py` step.
*   **Q: The dashboard or agents fail with Security Error on startup.**
    *   *A:* The `model.pkl` file has been modified or corrupted, causing the SHA-256 integrity check to fail. Re-run `python -m src.hero_agent.train_model` to generate a fresh model and matching `.sha256` hash.
*   **Q: Can I run this offline without internet access?**
    *   *A:* Yes. The dashboard image logo has been replaced with local components, and the threat classifier falls back to local vector search via ChromaDB and Sentence-Transformers if `GEMINI_API_KEY` is not present in your environment.

---

## 11. Future Work

*   **Distributed Stream Ingestion:** Integrate Apache Kafka or RabbitMQ as an ingestion broker to handle high-throughput network tapping streams instead of direct FastAPI REST invocations.
*   **ML Explainability Engine:** Incorporate native SHAP or LIME value visualizers on the dashboard to present exact mathematical contributions of flagged features to the Isolation Forest trees.
*   **Active CMDB Sync:** Connect the Supporting Agent's inventory to active infrastructure services (AWS Systems Manager, ServiceNow, VMware) to dynamically read asset properties and automatically execute containment API calls.

---

## 12. Submission Artifacts
*   **Pitch Presentation:** [PITCH_DECK.pptx](PITCH_DECK.pptx).
*   **Design Limitations:** [LIMITATIONS.md](docs/LIMITATIONS.md).
*   **MIT License details:** [LICENSE](LICENSE).

---

## 13. Acknowledgements
We would like to thank the organizers and judges of the **ET AI Hackathon 2026** for providing the opportunity to pitch this agentic cyber resilience solution.
