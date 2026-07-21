"use client";
import { Activity, ShieldAlert, Gauge, Timer } from "lucide-react";
import MetricCard from "@/components/MetricCard";
import AlertsFeed from "@/components/AlertsFeed";
import PendingApprovals from "@/components/PendingApprovals";
import ThreatAttributionPanel from "@/components/ThreatAttributionPanel";
import { useMetrics } from "@/hooks/useMetrics";

export default function DashboardPage() {
  const { metrics } = useMetrics();

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          label="Precision"
          value={metrics ? `${(metrics.precision * 100).toFixed(1)}%` : "—"}
          icon={Gauge}
          accent="safe"
        />
        <MetricCard
          label="Alerts (1h)"
          value={metrics?.alerts_last_hour ?? "—"}
          icon={Activity}
          accent="intel"
        />
        <MetricCard
          label="Pending Approvals"
          value={metrics?.pending_approvals ?? "—"}
          icon={ShieldAlert}
          accent="warning"
        />
        <MetricCard
          label="Inference Latency"
          value={metrics ? `${metrics.inference_latency_ms}ms` : "—"}
          icon={Timer}
          accent="intel"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <AlertsFeed />
        </div>
        <ThreatAttributionPanel />
      </div>

      <PendingApprovals />
    </div>
  );
}
