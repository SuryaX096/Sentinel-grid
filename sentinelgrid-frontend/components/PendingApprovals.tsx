"use client";
import { useAlerts } from "@/hooks/useAlerts";
import { Check, X } from "lucide-react";
import type { Alert } from "@/lib/types";

export default function PendingApprovals() {
  const { alerts, mutate } = useAlerts("pending");

  async function decide(alert: Alert, decision: "approve" | "dismiss") {
    // Optimistic update: pull this alert out of the pending list immediately,
    // then reconcile with the server response.
    mutate(alerts.filter((a) => a.id !== alert.id), false);
    await fetch("/api/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ alert_id: alert.id, decision }),
    });
    mutate();
  }

  return (
    <div className="rounded-lg border border-border bg-surface">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <span className="text-sm font-medium">Pending Human-in-the-Loop Approval</span>
        <span className="rounded-full bg-signal-warning/15 px-2 py-0.5 text-xs font-mono text-signal-warning">
          {alerts.length}
        </span>
      </div>
      {alerts.length === 0 && <p className="p-4 text-sm text-muted">Nothing waiting on you right now.</p>}
      {alerts.map((a) => (
        <div key={a.id} className="flex items-center justify-between border-b border-border/60 px-4 py-3">
          <div className="flex flex-col gap-0.5">
            <span className="font-mono text-sm">{a.playbook ?? "Containment action"}</span>
            <span className="text-xs text-muted">
              Asset {a.asset_id} · risk {a.risk_score}/100
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => decide(a, "approve")}
              className="flex items-center gap-1 rounded-md bg-signal-safe/15 px-3 py-1.5 text-xs font-medium text-signal-safe hover:bg-signal-safe/25"
            >
              <Check className="h-3.5 w-3.5" /> Approve
            </button>
            <button
              onClick={() => decide(a, "dismiss")}
              className="flex items-center gap-1 rounded-md bg-signal-critical/15 px-3 py-1.5 text-xs font-medium text-signal-critical hover:bg-signal-critical/25"
            >
              <X className="h-3.5 w-3.5" /> Dismiss
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
