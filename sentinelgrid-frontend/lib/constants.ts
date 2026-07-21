// Matches the 3s auto-refresh rate already established by the Streamlit SOC console,
// so behavior stays consistent across both dashboards during your demo.
export const REFRESH_INTERVAL_MS = 3000;

export const RISK_COLOR: Record<string, string> = {
  low: "text-signal-safe",
  medium: "text-signal-warning",
  high: "text-signal-critical",
  critical: "text-signal-critical",
};

export const RISK_BORDER: Record<string, string> = {
  low: "border-l-signal-safe",
  medium: "border-l-signal-warning",
  high: "border-l-signal-critical",
  critical: "border-l-signal-critical",
};
