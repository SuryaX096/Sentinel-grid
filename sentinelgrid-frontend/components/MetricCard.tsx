import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface Props {
  label: string;
  value: string | number;
  icon: LucideIcon;
  accent?: "safe" | "warning" | "critical" | "intel";
}

const ACCENT_MAP = {
  safe: "text-signal-safe",
  warning: "text-signal-warning",
  critical: "text-signal-critical",
  intel: "text-signal-intel",
};

export default function MetricCard({ label, value, icon: Icon, accent = "intel" }: Props) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border border-border bg-surface p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wide text-muted">{label}</span>
        <Icon className={cn("h-4 w-4", ACCENT_MAP[accent])} />
      </div>
      <span className="font-mono text-2xl font-semibold">{value}</span>
    </div>
  );
}
