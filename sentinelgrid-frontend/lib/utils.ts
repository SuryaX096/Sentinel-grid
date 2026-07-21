import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString("en-US", { hour12: false });
}

export function formatDuration(seconds: number) {
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
  return `${seconds.toFixed(1)}s`;
}

export function deriveRiskLevel(anomalyScore: number): "low" | "medium" | "high" | "critical" {
  if (anomalyScore >= 0.85) return "critical";
  if (anomalyScore >= 0.65) return "high";
  if (anomalyScore >= 0.4) return "medium";
  return "low";
}