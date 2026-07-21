"use client";
import { useAlerts } from "@/hooks/useAlerts";
import { useMemo } from "react";

export default function ThreatAttributionPanel() {
  const { alerts } = useAlerts();

  const tally = useMemo(() => {
    const counts = new Map<string, number>();
    for (const a of alerts) {
      if (!a.attack_technique) continue;
      counts.set(a.attack_technique, (counts.get(a.attack_technique) ?? 0) + 1);
    }
    return Array.from(counts.entries())
      .map(([technique, count]) => ({ technique, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 6);
  }, [alerts]);

  const max = Math.max(1, ...tally.map((t) => t.count));

  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="mb-3 text-sm font-medium">MITRE ATT&amp;CK Attribution</div>
      {tally.length === 0 && <p className="text-sm text-muted">No attributed techniques yet.</p>}
      <div className="flex flex-col gap-2">
        {tally.map((t) => (
          <div key={t.technique} className="flex items-center gap-3">
            <span className="w-28 shrink-0 truncate font-mono text-xs text-signal-intel">{t.technique}</span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-raised">
              <div className="h-full rounded-full bg-signal-intel" style={{ width: `${(t.count / max) * 100}%` }} />
            </div>
            <span className="w-6 shrink-0 text-right font-mono text-xs text-muted">{t.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}