// These mirror the Pydantic schemas in src/common/ of Cyber-resilience.
// Adjust field names here if your schema_validator.py differs.

export type AlertStatus = "pending" | "approved" | "dismissed" | "auto_resolved";
export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface MitreAttribution {
  technique_id: string;      // e.g. "T1071.001"
  technique_name: string;    // e.g. "Application Layer Protocol"
  tactic: string;            // e.g. "Command and Control"
  confidence: number;        // 0-1, from Gemini/ChromaDB validation
}

export interface Alert {
  id: string;
  timestamp: string;         // ISO 8601
  source_ip: string;
  dest_ip: string;
  asset_id: string;
  anomaly_score: number;     // Isolation Forest output
  risk_score: number;        // 0-100, computed by supporting_agent
  risk_level: RiskLevel;
  mitre: MitreAttribution | null;
  cve_refs: string[];
  status: AlertStatus;
  playbook: string | null;   // recommended containment action
}

export interface Metrics {
  precision: number;
  recall: number;
  f1_score: number;
  false_positive_rate: number;
  accuracy: number;
  mttd_seconds: number;
  mttr_seconds: number;
  inference_latency_ms: number;
  alerts_last_hour: number;
  pending_approvals: number;
}

export interface ApproveRequest {
  alert_id: string;
  decision: "approve" | "dismiss";
  analyst_note?: string;
}
