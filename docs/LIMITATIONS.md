# System Design Assumptions & Limitations
**SentinelMind AI - Cyber Resilience Platform (Prototype)**

Every prototype makes design trade-offs to demonstrate feasibility within a short timeframe. Below is an honest, comprehensive list of the constraints, mock aspects, and architectural limitations of this system.

---

## 1. Machine Learning & Anomaly Detection (Hero Agent)

*   **Public Dataset Benchmark:** The Hero Agent is trained and evaluated on the **NSL-KDD dataset**, which represents network connection flow vectors from 1999 (with updates). While excellent for prototype verification, actual corporate networks feature modern protocols, higher traffic density, and complex cloud infrastructure flows that are not captured here.
*   **Static Isolation Forest:** The trained `IsolationForest` is serialized into `model.pkl`. In a production setting, connection patterns drift daily. The model would require an active feedback loop, incremental learning pipelines, or dynamic retraining jobs to prevent high false-positive rates due to network configuration shifts.
*   **Heuristic Feature Explanations:** Outlier features are flagged based on simple Z-score thresholds relative to the training set's baseline normal traffic. While highly effective, it does not represent ML-native model explainability (such as SHAP or LIME values), which would show feature contributions to the Isolation Forest splits.

---

## 2. Threat Attribution (Attribution Agent)

*   **Simplified Technique Index:** The vector store (`chroma_store/`) contains a curated index of 9 core MITRE ATT&CK techniques rather than the entire 600+ Enterprise Techniques list. This is done to ensure high semantic clarity in the prototype demo, but a production pipeline would query the full live MITRE STIX JSON feed.
*   **Dual-Mode Reliability:** While the LLM Validation Mode (Gemini API) provides high-quality explanations, the local similarity matching mode (default) relies strictly on text distance in embedding space. Certain anomalous feature sets might yield borderline semantic similarity, leading to potential misattribution if the threshold is set too low.
*   **Rule-Based Translators:** `feature_to_text.py` is a deterministic template-based mapper. In production, this translation would need to handle multi-protocol contexts and parse raw payload packets directly.

---

## 3. Incident Orchestration & Response (Supporting Agent)

*   **Simulated Assets & Playbooks:** Playbooks (like `isolate_endpoint` or `rate_limit_ip`) are simulated. The orchestrator updates the alert status and logs actions to the `audit_trail` but does not trigger actual hypervisor API calls (e.g. AWS Security Group updates or VMware vSphere API calls) to isolate endpoints.
*   **Static Asset Catalog:** The asset inventory (`asset_inventory.json`) is a mock list. A production environment would integrate with a dynamic asset discovery tool or CMDB (Configuration Management Database) like ServiceNow or AWS Systems Manager.
*   **Vulnerability Priority Boost:** The prioritization boost relies on manual CVE match heuristics. A production system would ingest vulnerability metrics dynamically from scanners like Tenable or Qualys.

---

## 4. Operational & Deployment Constraints

*   **Microservices Architecture overhead:** Running three separate FastAPI APIs on localhost (`8001`, `8002`, `8003`) is excellent for showcasing microservice separation but adds communication latency (HTTP POST overhead). For high-performance network tapping, these agent pipelines would be combined inside a single process or message broker (like Kafka/RabbitMQ) worker.
*   **Gated Human Approvals:** High-blast-radius actions pause in `pending_approval` state. In a real SOC, these must either timeout/escalate automatically if no analyst responds within a SLA (e.g. 5 minutes) to prevent threat spread.
