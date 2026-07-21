// Mirrors your actual AlertSchema (src/common) exactly.

export interface AuditEntry {
  timestamp: string;
  agent: string;
  action: string;
  notes: string;
}

export interface Alert {
  alert_id: string;
  timestamp: string;
  entity: string;
  anomaly_score: number;
  features_flagged: string[];
  attack_technique: string | null;
  technique_confidence: number | null;
  response_action: string | null;
  response_status: string;
  audit_trail: AuditEntry[];
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