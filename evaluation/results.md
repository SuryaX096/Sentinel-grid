
## Hero Agent Anomaly Detection Evaluation

**Date:** 2026-07-18
**Model Type:** Isolation Forest (trained on normal traffic only)
**Tuned Score Threshold:** `0.4800`

### Performance Summary Table

| Metric | Score (Value) | Percentage | Description |
|---|---|---|---|
| **Precision** | `0.9582` | 95.82% | Proportion of flagged alerts that were actual attacks |
| **Recall (Sensitivity)** | `0.7447` | 74.47% | Proportion of actual attacks successfully detected |
| **F1-Score** | `0.8381` | - | Harmonic mean of precision and recall |
| **False Positive Rate (FPR)** | `0.0429` | 4.29% | Rate at which normal traffic is misidentified as anomalous |
| **False Negative Rate (FNR)** | `0.2553` | 25.53% | Rate at which attacks slip through undetected |

### Confusion Matrix Counts

*   **True Negatives (TN):** `9294` (Normal traffic correctly identified)
*   **False Positives (FP):** `417` (Normal traffic flagged as anomaly)
*   **False Negatives (FN):** `3276` (Attacks that went undetected)
*   **True Positives (TP):** `9557` (Attacks correctly flagged)

### Detection Breakdown by Attack Class

| Attack Class | Count (N) | Isolation/Detection Rate | Action Performance |
|---|---|---|---|
| **Normal (Inliers)** | 9711 | 95.71% | Clean Baseline Preservation |
| **DoS (Denial of Service)** | 7458 | 88.13% | Volumetric Mitigation Triggered |
| **Probe (Scanning)** | 2421 | 99.59% | Port/IP Scanning Throttling |
| **R2L (Unauthorized Access)** | 2887 | 19.12% | Credential Abuse Blocking |
| **U2R (Privilege Escalation)** | 67 | 31.34% | Endpoint Isolation Escalation |


## Attribution Agent Threat Classification Evaluation

**Date:** 2026-07-18
**Attribution Mode:** Local Semantic Similarity Search (ChromaDB candidate retrieval)
**Embedding Model:** `all-MiniLM-L6-v2`
**Benchmark Size:** 20 Scenarios

### Performance Metrics Summary

*   **Overall Classification Accuracy:** `65.00%` (13 of 20 cases matched correctly)
*   **Total Test Cases Evaluated:** `20`

### Scenario Test Runs Breakdown

| ID | Flagged Features | Expected Technique ID | Predicted Technique ID | Predicted Technique Name | Similarity | Status |
|---|---|---|---|---|---|---|
| 1 | `serror_rate, count` | **T1498** | **T1498** | Network Service Denial | `53.21%` | 🟢 PASS |
| 2 | `srv_serror_rate, count` | **T1498** | **T1498** | Network Service Denial | `56.62%` | 🟢 PASS |
| 3 | `serror_rate, srv_serror_rate` | **T1498** | **T1498** | Network Service Denial | `54.05%` | 🟢 PASS |
| 4 | `wrong_fragment` | **T1499** | **T1499** | Endpoint Denial of Service | `51.34%` | 🟢 PASS |
| 5 | `wrong_fragment, duration` | **T1499** | **T1499** | Endpoint Denial of Service | `54.96%` | 🟢 PASS |
| 6 | `land` | **T1499** | **T1595** | Active Scanning | `40.87%` | 🔴 FAIL |
| 7 | `diff_srv_rate, dst_host_diff_srv_rate` | **T1046** | **T1046** | Network Service Scanning | `61.14%` | 🟢 PASS |
| 8 | `dst_host_diff_srv_rate` | **T1046** | **T1595** | Active Scanning | `52.25%` | 🔴 FAIL |
| 9 | `srv_diff_host_rate` | **T1595** | **T1498** | Network Service Denial | `40.40%` | 🔴 FAIL |
| 10 | `dst_host_srv_diff_host_rate` | **T1595** | **T1595** | Active Scanning | `58.04%` | 🟢 PASS |
| 11 | `num_failed_logins, count` | **T1110** | **T1110** | Brute Force | `65.86%` | 🟢 PASS |
| 12 | `num_failed_logins, logged_in` | **T1110** | **T1110** | Brute Force | `64.95%` | 🟢 PASS |
| 13 | `num_failed_logins` | **T1110** | **T1110** | Brute Force | `66.22%` | 🟢 PASS |
| 14 | `src_bytes, duration` | **T1190** | **T1498** | Network Service Denial | `54.11%` | 🔴 FAIL |
| 15 | `dst_bytes, duration` | **T1190** | **T1498** | Network Service Denial | `53.86%` | 🔴 FAIL |
| 16 | `logged_in, duration, service` | **T1133** | **T1110** | Brute Force | `55.09%` | 🔴 FAIL |
| 17 | `root_shell, su_attempted` | **T1068** | **T1068** | Exploitation for Privilege Escalation | `65.08%` | 🟢 PASS |
| 18 | `root_shell, num_compromised` | **T1068** | **T1068** | Exploitation for Privilege Escalation | `64.64%` | 🟢 PASS |
| 19 | `su_attempted, num_access_files` | **T1548** | **T1548** | Abuse Elevation Control Mechanism | `64.31%` | 🟢 PASS |
| 20 | `num_access_files, num_shells` | **T1548** | **T1068** | Exploitation for Privilege Escalation | `49.01%` | 🔴 FAIL |
