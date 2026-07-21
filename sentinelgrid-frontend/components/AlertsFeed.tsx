"use client";
import { useAlerts } from "@/hooks/useAlerts";
import { RISK_BORDER } from "@/lib/constants";
import { formatTime, cn } from "@/lib/utils";

export default function AlertsFeed() {
  const { alerts, isLoading, isError } = useAlerts();

  if (isError) {
    return (
      <p className="text-sm text-signal-critical">
        Can&apos;t reach the read agent — check backend-addition/read_api.py is running on :8004.
      </p>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-surface">
      <div className="border-b border-border px-4 py-3 text-sm font-medium">Live Alert Feed</div>
      <div className="max-h-96 overflow-y-auto scrollbar-thin">
        {isLoading && <p className="p-4 text-sm text-muted">Loading…</p>}
        {!isLoading && alerts.length === 0 && (
          <p className="p-4 text-sm text-muted">No alerts yet — start the replay simulator.</p>
        )}
        {alerts.map((a) => (
          <div
            key={a.id}
            className={cn(
              "flex items-center justify-between border-l-2 border-b border-border/60 px-4 py-3",
              RISK_BORDER[a.risk_level]
            )}
          >
            <div className="flex flex-col gap-0.5">
              <span className="font-mono text-sm">
                {a.source_ip} → {a.dest_ip}
              </span>
              <span className="text-xs text-muted">
                {a.mitre ? `${a.mitre.technique_id} · ${a.mitre.technique_name}` : "Attribution pending"}
              </span>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <span className="font-mono text-muted">{formatTime(a.timestamp)}</span>
              <span className="rounded-full bg-raised px-2 py-1 font-mono uppercase text-muted">
                {a.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
