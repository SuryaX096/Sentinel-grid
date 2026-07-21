"use client";
import { useMetrics } from "@/hooks/useMetrics";
import { formatDuration } from "@/lib/utils";

export default function Topbar() {
  const { metrics } = useMetrics();

  return (
    <header className="flex items-center justify-between border-b border-border px-6 py-4">
      <div>
        <h1 className="text-lg font-semibold">SOC Console</h1>
        <p className="text-xs text-muted">Problem Statement 7 — AI-Driven Cyber Resilience</p>
      </div>
      <div className="flex items-center gap-6 font-mono text-xs text-muted">
        <span>
          MTTD <span className="text-foreground">{metrics ? formatDuration(metrics.mttd_seconds) : "—"}</span>
        </span>
        <span>
          MTTR <span className="text-foreground">{metrics ? formatDuration(metrics.mttr_seconds) : "—"}</span>
        </span>
      </div>
    </header>
  );
}
